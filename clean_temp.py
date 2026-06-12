import sys, os

project_root = r"C:\gym_django\gym_django\gym_django\gym_django\gym_django\gym_dangoo (1)\gym_djangoo (1)\gym_django\gym"
keep = {'manage.py', '__init__.py', 'settings.py', 'urls.py', 'wsgi.py', 'clean_temp.py'}
diagnostics = [f for f in os.listdir(project_root) if f.endswith('.py') and f not in keep]
for f in diagnostics:
    os.remove(os.path.join(project_root, f))
    print(f"Removed: {f}")
print(f"Cleaned {len(diagnostics)} temp .py files")

# Clean up C: root too
try:
    for f in os.listdir('C:/'):
        if f == 'clean_temp.py':
            os.remove(f'C:/{f}')
            print(f"Removed C:/{f}")
except: pass

print("Done")