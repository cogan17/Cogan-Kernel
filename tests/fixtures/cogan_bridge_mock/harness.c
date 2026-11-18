/* Runs kernel/patches/cogan_bridge.c against kmock.h: a CPU limit release that fails is tried again
 * (audit 2026-11-18, T4). Built and run by tests/test_cogan_bridge_qos.py. */
#include "cogan_bridge.c"

#define CHECK(cond) do { if (!(cond)) { fprintf(stderr, "line %d: %s\n", __LINE__, #cond); exit(1); } } while (0)
#define LITTLE (&mock_policies[0].constraints)
#define BIG (&mock_policies[1].constraints)

static int limit(const char *text)
{
	return (int)limits_store(NULL, &limits_attr, text, strlen(text));
}

static int run_work(void)  /* the watchdog, when it is pending; 1 if it ran */
{
	if (!cogan_work.pending)
		return 0;
	cogan_work.pending = 0;
	cogan_work.fn(&cogan_work.work);
	return 1;
}

static bool released(void)
{
	return LITTLE->max_value == FREQ_QOS_MAX_DEFAULT_VALUE && BIG->max_value == FREQ_QOS_MAX_DEFAULT_VALUE;
}

int main(void)
{
	char buf[PAGE_SIZE];
	int runs;

	CHECK(cogan_init() == 0);
	CHECK(released());

	/* 1. The release at the end of the TTL fails once for the big cluster, then works. */
	CHECK(limit("50 60 10") > 0);
	CHECK(BIG->max_value == 1500000 && LITTLE->max_value == 1200000 && cogan_work.pending);
	BIG->fail_release = 1;
	mock_now += 11;
	CHECK(run_work());
	CHECK(BIG->max_value == 1500000 && LITTLE->max_value == FREQ_QOS_MAX_DEFAULT_VALUE);
	CHECK(last_error == -EBUSY && cogan_work.pending);  /* old code: nothing pending, stuck at 1.5 GHz */
	limits_show(NULL, &limits_attr, buf);
	CHECK(strstr(buf, " 0 2 -16\n") != NULL);  /* TTL 0, 2 policies, the error kept for the WebUI */
	CHECK(run_work());
	CHECK(released() && last_error == 0 && !cogan_work.pending);  /* back to default, the watchdog stops */

	/* 2. A release that keeps failing is tried a bounded number of times, then the watchdog stops. */
	CHECK(limit("40 40 5") > 0);
	BIG->fail_release = 1000;  /* always */
	mock_now += 6;
	for (runs = 0; run_work(); runs++)
		CHECK(runs < 100);
	CHECK(runs == 1 + COGAN_RELEASE_RETRIES);
	CHECK(BIG->max_value == 1200000 && last_error == -EBUSY);
	/* A later write starts over and can release it. */
	BIG->fail_release = 0;
	CHECK(limit("0 0 0") > 0);
	CHECK(released() && !cogan_work.pending);

	/* 3. A failed write: the limit is undone at once, and an undo that fails is tried again too. */
	BIG->fail_limit = 1;      /* the big cluster refuses the new limit */
	LITTLE->fail_release = 1; /* and the little one its undo */
	CHECK(limit("50 60 10") == -EBUSY);
	CHECK(LITTLE->max_value == 1200000 && cogan_work.pending);
	CHECK(run_work());
	CHECK(released() && !cogan_work.pending);

	/* 4. Nothing failed: no extra watchdog runs once the limit is released. */
	CHECK(limit("80 80 5") > 0);
	mock_now += 6;
	CHECK(run_work() && released() && !cogan_work.pending);
	puts("OK");
	return 0;
}
