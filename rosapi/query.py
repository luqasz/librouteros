# -*- coding: UTF-8 -*-

from words import queryWord, attributeWord

class query:

    def __init__( self ):
        self._sentence = []

    def where( self, expression ):
        self._sentence.append( expression )
        return self

    def returning( self, attrs ):
        attrs = ','.join( attrs )
        self._sentence.append( attributeWord( '=.proplist=' + attrs ) )
        return self

    def having( self, prop ):
        self._sentence.append( queryWord( '?' + prop.name ) )
        return self

    def not_having( self, prop ):
        self._sentence.append( queryWord( '?-' + prop.name ) )
        return self

    def __iter__( self ):
        return iter( self._sentence )

    def __getattr__( self, name ):
        setattr( self, name, queryWord( name ) )
        return getattr( self, name )

    def __repr__( self ):
        return '<query {self._sentence!r}>'.format( self = self )
#
# DESCRIPTORY
#
#
# class FooType( type ):
#     def _foo_func( cls ):
#         return 'foo!'
#
#     def _bar_func( cls ):
#         return 'bar!'
#
#     def __getattr__( cls, key ):
#         if key == 'Foo':
#             return cls._foo_func()
#         elif key == 'Bar':
#             return cls._bar_func()
#         raise AttributeError( key )
#
#     def __str__( cls ):
#         return 'custom str for %s' % ( cls.__name__, )
#
# class MyClass( metaclass = FooType ):
#     pass
