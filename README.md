# dice
Simple python implementation of tabletop dicerolls


## Usage

```
from dice import *

>>> x = 3 * d6 + 2 * d10 + 4
>>> r = x.roll()
>>> r.total
24

>>> print(r.pretty(2))
     2d10 : 10  = 7 + 3
 +    3d6 : 10  = 1 + 4 + 5
 +      4 : 4
---------------
 =          24


>>> [int(2 + 2*d(10)) for _ in range(10)]
[15, 19, 6, 7, 6, 11, 18, 18, 13, 18]
```

## Development

Run tests:

```
python3 -m doctest -v dice/dice.py
```


## See also

- [python-dice](https://github.com/borntyping/python-dice) - a mature python dice library with py2 compatibility
