import requests

url = "https://api.dynamic.reports.employment.gov.au/anonap/extensions/hSKLS02_SkillSelect_EOI_Data/hSKLS02_SkillSelect_EOI_Data.js"
resp = requests.get(url, timeout=30)
resp.raise_for_status()
open('d:/Interlace_DataAnalyst/Scrapping-Model/hSKLS02_SkillSelect_EOI_Data.js','wb').write(resp.content)
print('saved', len(resp.content))
