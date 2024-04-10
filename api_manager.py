import os
import importlib


apis = {}

for module in [m[:-3] for m in os.listdir('./apis') if m.endswith('.py')]:
    mod = importlib.import_module('apis.'+module)
    for key in mod.api.keys():
        apis[key] = mod.api[key]
