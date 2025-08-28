import os, datetime, pathlib
def app(p):
    return f"\n---\n### {os.path.basename(p)}\n\n```\n" + open(p, 'r', errors='ignore').read() + "\n```\n"
root='docs/diagnostics_v1'
sections=[
 'showmigrations.txt','models_list.txt','table_counts.txt','integrity.txt',
 'audit_video_clips.txt',
 'csv_headers.json','csvexercise_fields.txt','grep_csvexercise.txt','grep_ai_tags.txt',
 'grep_onboarding_processor.txt','grep_prompt_manager.txt','grep_plan_services.txt','grep_extra_fields.txt',
 'env_r2_settings.txt','duration_sanity.txt',
 'templates_presence.txt','urls_presence.txt','report_creation_smoketest.txt'
]
body=''
for s in sections:
    p=os.path.join(root,s)
    if os.path.exists(p):
        body+=app(p)
md='docs/diagnostics_v1.md'
with open(md, 'a') as f:
    f.write('\n\n## 📎 Приложения (сырые результаты)\n')
    f.write(body)
    f.write(f"\n\n---\nДата: {datetime.datetime.now().isoformat()}\n")