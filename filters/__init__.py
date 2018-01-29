import os

from filter import ItemFilter

__all__ = []

for module in os.listdir(os.path.dirname(__file__)):
   if module == '__init__.py' or module[-3:] != '.py':
        continue
   module_name = module[:-3]
   m = __import__(module_name, locals(), globals() )
   for name in dir(m):
      c = getattr(m,name)
      if type(c) is type and issubclass(c,ItemFilter):
         globals()[ c.__name__ ] = c
         __all__.append( c.__name__ )
