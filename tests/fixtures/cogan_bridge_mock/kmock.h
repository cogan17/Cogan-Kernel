/* Just enough of the kernel API for kernel/patches/cogan_bridge.c to run in user space (tests only). */
#ifndef KMOCK_H
#define KMOCK_H
#include <errno.h>
#include <limits.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

typedef uint64_t u64;
typedef int32_t s32;
#define S32_MAX INT32_MAX
#define __init
#define late_initcall(fn)
#define HZ 100
#define PAGE_SIZE 4096
#define GFP_KERNEL 0
#define IS_ENABLED(x) 0
#define CAP_SYS_ADMIN 21
#define NOTIFY_OK 1
#define CPUFREQ_POLICY_NOTIFIER 1
#define CPUFREQ_CREATE_POLICY 3
#define CPUFREQ_REMOVE_POLICY 4
#define min(a, b) ((a) < (b) ? (a) : (b))
#define max(a, b) ((a) > (b) ? (a) : (b))
#define max_t(t, a, b) ((t)(a) > (t)(b) ? (t)(a) : (t)(b))
#define container_of(ptr, type, member) ((type *)((char *)(ptr) - offsetof(type, member)))

struct list_head { struct list_head *next, *prev; };
#define LIST_HEAD(name) struct list_head name = { &(name), &(name) }
static inline bool list_empty(const struct list_head *h) { return h->next == h; }
static inline void list_add_tail(struct list_head *n, struct list_head *h)
{ n->prev = h->prev; n->next = h; h->prev->next = n; h->prev = n; }
static inline void list_del(struct list_head *n) { n->prev->next = n->next; n->next->prev = n->prev; }
#define list_for_each_entry(pos, head, member) \
	for (pos = container_of((head)->next, __typeof__(*pos), member); &pos->member != (head); \
	     pos = container_of(pos->member.next, __typeof__(*pos), member))
#define list_for_each_entry_safe(pos, n, head, member) \
	for (pos = container_of((head)->next, __typeof__(*pos), member), \
	     n = container_of(pos->member.next, __typeof__(*pos), member); &pos->member != (head); \
	     pos = n, n = container_of(n->member.next, __typeof__(*n), member))

struct mutex { int held; };
#define DEFINE_MUTEX(name) struct mutex name = { 0 }
static inline void mutex_lock(struct mutex *m) { if (m->held++) { fprintf(stderr, "deadlock\n"); abort(); } }
static inline void mutex_unlock(struct mutex *m) { m->held--; }

static inline void *kzalloc(size_t size, int flags) { (void)flags; return calloc(1, size); }
static inline void kfree(void *p) { free(p); }
static inline bool capable(int cap) { (void)cap; return true; }
static inline int kstrtouint(const char *s, unsigned int base, unsigned int *res)
{ char *end; unsigned long v = strtoul(s, &end, base); if (end == s) return -EINVAL; *res = v; return 0; }

/* Clock and work: the test moves the clock and runs the pending work itself. */
static u64 mock_now;
static inline u64 ktime_get_boottime_seconds(void) { return mock_now; }
struct work_struct { int unused; };
struct delayed_work { struct work_struct work; void (*fn)(struct work_struct *); int pending; };
#define DECLARE_DEFERRABLE_WORK(name, f) struct delayed_work name = { { 0 }, f, 0 }
struct workqueue_struct;
static struct workqueue_struct *system_wq;
static inline bool mod_delayed_work(struct workqueue_struct *wq, struct delayed_work *w, unsigned long d)
{ (void)wq; (void)d; w->pending = 1; return true; }
static inline bool schedule_delayed_work(struct delayed_work *w, unsigned long d)
{ (void)d; w->pending = 1; return true; }

/* Frequency QoS: a request can be told to fail the next lowering or the next release. */
enum freq_qos_req_type { FREQ_QOS_MIN = 1, FREQ_QOS_MAX };
#define FREQ_QOS_MAX_DEFAULT_VALUE S32_MAX
struct freq_constraints { s32 max_value; int fail_limit, fail_release, updates; };
struct freq_qos_request { struct freq_constraints *qos; s32 value; };
static inline int freq_qos_add_request(struct freq_constraints *q, struct freq_qos_request *r,
				       enum freq_qos_req_type t, s32 v)
{ (void)t; r->qos = q; r->value = v; q->max_value = v; return 0; }
static inline int freq_qos_update_request(struct freq_qos_request *r, s32 v)
{
	int *fail = v == FREQ_QOS_MAX_DEFAULT_VALUE ? &r->qos->fail_release : &r->qos->fail_limit;

	r->qos->updates++;
	if (*fail > 0) {
		if (*fail < 1000)
			(*fail)--;
		return -EBUSY;
	}
	r->value = v; r->qos->max_value = v;
	return 0;
}
static inline int freq_qos_remove_request(struct freq_qos_request *r) { (void)r; return 0; }
static inline s32 freq_qos_read_value(struct freq_constraints *q, enum freq_qos_req_type t) { (void)t; return q->max_value; }

struct cpufreq_cpuinfo { unsigned int min_freq, max_freq; };
struct cpufreq_policy { unsigned int cpu; struct cpufreq_cpuinfo cpuinfo; struct freq_constraints constraints; };
struct notifier_block { int (*notifier_call)(struct notifier_block *, unsigned long, void *); };
#define NR_MOCK_CPUS 2
static struct cpufreq_policy mock_policies[NR_MOCK_CPUS] = {
	{ 0, { 500000, 2000000 }, { 0 } }, { 4, { 600000, 3000000 }, { 0 } } };
#define for_each_possible_cpu(cpu) for ((cpu) = 0; (cpu) < NR_MOCK_CPUS; (cpu)++)
static inline struct cpufreq_policy *cpufreq_cpu_get(unsigned int i) { return &mock_policies[i]; }
static inline void cpufreq_cpu_put(struct cpufreq_policy *p) { (void)p; }
static inline void cpus_read_lock(void) {}
static inline void cpus_read_unlock(void) {}
static inline int cpufreq_register_notifier(struct notifier_block *nb, unsigned int l) { (void)nb; (void)l; return 0; }
static inline int cpufreq_unregister_notifier(struct notifier_block *nb, unsigned int l) { (void)nb; (void)l; return 0; }

struct kobject { int unused; };
static struct kobject mock_kobj, *kernel_kobj = &mock_kobj;
struct attribute { const char *name; unsigned short mode; };
struct kobj_attribute {
	struct attribute attr;
	ssize_t (*show)(struct kobject *, struct kobj_attribute *, char *);
	ssize_t (*store)(struct kobject *, struct kobj_attribute *, const char *, size_t);
};
#define __ATTR(n, m, s, st) { { #n, m }, s, st }
struct attribute_group { struct attribute **attrs; };
static inline struct kobject *kobject_create_and_add(const char *n, struct kobject *p) { (void)n; return p; }
static inline void kobject_put(struct kobject *k) { (void)k; }
static inline int sysfs_create_group(struct kobject *k, const struct attribute_group *g) { (void)k; (void)g; return 0; }
static inline int sysfs_emit(char *buf, const char *fmt, ...)
{ va_list a; int n; va_start(a, fmt); n = vsnprintf(buf, PAGE_SIZE, fmt, a); va_end(a); return n; }
static inline int sysfs_emit_at(char *buf, int at, const char *fmt, ...)
{ va_list a; int n; va_start(a, fmt); n = vsnprintf(buf + at, PAGE_SIZE - at, fmt, a); va_end(a); return n; }
static const char linux_banner[] = "Linux version mock\n";
#endif
