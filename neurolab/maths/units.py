from neurolab.db import *

bases = {
    'S': 'siemen(s)',
    'F': 'farad(s)',
    'A': 'ampere(s)',
    'V': 'volt(s)',
    'Ohm': 'ohm(s)',
    'N': 'newton(s)',
    'lb': 'pound(s)',
    'g': 'gram(s)',
    'J': 'joule(s)',
    'rad': 'radian(s)',
    'cd': 'candela(s)',
    'mol': 'mole(s)',
    'M': 'molar',
    'W': 'watt(s)',
    'Pa': 'pascal(s)',
}

SI_MULTIPLIERS = {
    'f': 1e-15,
    'p': 1e-12,
    'n': 1e-9,
    'mc': 1e-6,
    'm': 1e-3,
    'k': 1e3,
    'M': 1e6,
    'G': 1e9,
    'T': 1e12,
    'P': 1e15,
}
TIME_MULTIPLIERS = {
    'fs': 1e-15,
    'ps': 1e-12,
    'ns': 1e-9,
    'mcs': 1e-6,
    'ms': 1e-3,
    'm': 60.0,
    'h': 60.0**2,
    'd': 60.0**2*24,
    'wk': 60.0**2*24*7,
}

def unit_aliases(base, multipliers, extras=None):
    base = {
        '%s%s' % (m, base): v
        for m,v in multipliers.iteritems()
    }
    base.update(extras or {})
    return base


class Unit(Document):
    key = StringField()
    name = StringField()
    aliases = DictField()
    
    def __repr__(self):
        return "<Unit: %s>" % self.name
    
    
    @classmethod
    def predefine(cls, **kwargs):
        key = kwargs['key']
        obj = cls.objects(key=key)
        if obj.count() == 0:
            obj = cls(**kwargs)
            obj.save()
        else:
            obj = obj[0]
        
        return obj
    


for key, name in bases.iteritems():
    locals()[key] = Unit.predefine(key=key, name=name, aliases=unit_aliases(key, SI_MULTIPLIERS))

m = Unit.predefine(key='m', name='meter(s)', 
    aliases=unit_aliases('m', SI_MULTIPLIERS, 
    {'pc': 3.085674008015063e16, 'ly': 9.4607304725808e15, 'AU': 1.495978707e11}))
K = Unit.predefine(key='K', name='kelvin(s)')
s = Unit.predefine(key='s', name='second(s)', aliases=TIME_MULTIPLIERS)
