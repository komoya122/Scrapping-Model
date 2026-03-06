import json

with open("data/output/hc_raw.json", "r") as f:
    hc = json.load(f)

print("Master Measure:", hc.get("qMeasures", [{}])[0].get("qFallbackTitle"))

target_titles = ["As At Month", "Visa Type", "EOI Status", "Occupation", "Points", "Nominated State"]

selected_dims = []

for idx, dim in enumerate(hc.get("qDimensions", [])):
    title = dim.get("qFallbackTitle")
    print(f"[{idx}] {title}")
    if title in target_titles:
        selected_dims.append(dim)
        
print(f"\nFound {len(selected_dims)} out of {len(target_titles)} target columns.")
for d in selected_dims:
    print(" ->", d.get("qFallbackTitle"))
