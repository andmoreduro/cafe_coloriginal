import importlib
import inspect

from django.contrib import admin

models_module = importlib.import_module(".models", "sistema_transaccional")
class_list = [cls for cls in dir(models_module) if inspect.isclass(getattr(models_module, cls))]
for cls in class_list:
    admin.site.register(getattr(models_module, cls))