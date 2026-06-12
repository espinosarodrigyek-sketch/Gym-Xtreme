import sys, os

project_root = r"C:\gym_django\gym_django\gym_django\gym_django\gym_django\gym_dangoo (1)\gym_djangoo (1)\gym_django\gym"
diagnostics = [f for f in os.listdir(project_root) if f.endswith('.py') and f not in ('manage.py','__init__.py','settings.py','urls.py','wsgi.py')]
for f in diagnostics:
    os.remove(os.path.join(project_root, f))
    print(f"Removed: {f}")
print(f"Cleaned {len(diagnostics)} files")
# Also clean up the root-level file
try:
    os.remove('C:/clean_temp.py')
    print("Removed C:/clean_temp.py")
except: pass
print("Done")