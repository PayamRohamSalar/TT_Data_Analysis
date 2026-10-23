import json

path_compact = r"C:\Users\Payam\.gemini\antigravity\brain\8826e6c0-7015-4e16-8ab1-0ac09d0d5b65\.system_generated\logs\transcript.jsonl"
path_full = r"C:\Users\Payam\.gemini\antigravity\brain\8826e6c0-7015-4e16-8ab1-0ac09d0d5b65\.system_generated\logs\transcript_full.jsonl"

with open(path_compact, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f):
        data = json.loads(line)
        if data.get("type") == "USER_INPUT":
            content = data.get("content", "")
            if "پرامپت داوری مستقل (دور دوم)" in content:
                print(f"Compact step {idx}: length {len(content)}, truncated: {data.get('truncated_fields')}")
                if data.get('truncated_fields'):
                    # read corresponding line in full
                    with open(path_full, "r", encoding="utf-8") as f_full:
                        for fidx, fline in enumerate(f_full):
                            if fidx == idx:
                                fdata = json.loads(fline)
                                full_content = fdata.get("content", "")
                                print(f"Full step {fidx}: length {len(full_content)}")
                                with open("reports/review_S1_S5b/results/user_prompt_round2.txt", "w", encoding="utf-8") as out:
                                    out.write(full_content)
                                print("Wrote full content.")
                                break
