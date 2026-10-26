# Which thermal zones the controller reads (needs thermal.awk first). Input: "<zone dir> <type>".
# Output: "main:<dir>" for CPU and GPU sensors, "skin:<dir>" for the phone body, "other:<dir>" for the
# rest, grouped exactly like the shared decoder (sensors.awk) groups them.
{
    name = $2; gsub(/[^A-Za-z0-9_.+-]/, "_", name)
    if (NF < 2 || name == "") next
    g = group(name)
    print (g == "cpu" || g == "gpu" ? "main" : g == "skin" ? "skin" : "other") ":" $1
}
