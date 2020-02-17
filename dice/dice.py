import random
from collections import Counter
from typing import Dict, List, Union, Optional


class Dice:
    @staticmethod
    def parse_string(s):
        """
        TODO: too permissive. Error on malformed inputs
        """
        parts = [p.strip() for p in s.split('+')]
        counter = Counter()
        constant = 0
        for part in parts:
            if 'd' in part:
                l, r = part.split('d')
                counter[int(r)] += int(l)
            else:
                constant += int(part)
        return counter, constant

    @classmethod
    def from_string(cls, s):
        """
        >>> Dice.from_string('3d6 + 2')
        Dice("3d6 + 2")
        """
        counter, constant = cls.parse_string(s)
        return Dice(dice=counter, constant=constant)

    @classmethod
    def empty(cls):
        return cls(dice=None, constant=0)

    @classmethod
    def one(cls, dice_size: int):
        return cls(dice=Counter({dice_size: 1}), constant=0)

    def __init__(self,
                 s: Optional[str] = None,
                 dice: Optional[Counter] = None,
                 constant: int = 0):
        """
        Represents zero or more dice to be rolled together. Default state
        is just a constant term of 0.

        :param s: A dice string, included to make repr behave nicely.
        :param dice: Possibly empty counter like {size of dice: number of dice}
        :param constant: Constant offset applied to this set of dice... acts like "d(1)".
        """
        assert not (s and (dice or constant)), \
            "Dice should be initialized with a string OR a counter and constant"
        if s:
            dice, constant = self.parse_string(s)

        assert all([k > 0 for k in dice.keys()]), "Dice sizes must be positive integers"
        self.dice: Counter = dice or Counter()
        self.constant = constant

    def __repr__(self):
        """
        >>> 3 * d(6) + 2
        Dice("3d6 + 2")
        """
        return f'{self.__class__.__name__}("{self!s}")'

    def __str__(self):
        """
        >>> print(str(3 * d(6) + 2))
        3d6 + 2
        """
        dice_part = ' + '.join(
            f'{n_dice}d{dice_size}'
            for (dice_size, n_dice) in sorted(self.dice.items(), reverse=True)
        )
        if dice_part:
            if self.constant > 0:
                const_part = f' + {self.constant}'
            else:
                const_part = ''
        else:
            const_part = str(self.constant)
        return f'{dice_part}{const_part}'

    def __rmul__(self, other: int) -> 'Dice':
        """
        >>> dict((3 * d(6)).dice)
        {6: 3}
        """
        if isinstance(other, int):
            new_dice = self.dice.copy()
            for dice_size in new_dice:
                new_dice[dice_size] = other * new_dice[dice_size]
            return Dice(dice=new_dice, constant=other * self.constant)
        else:
            raise NotImplementedError

    def __add__(self, other) -> 'Dice':
        """
        >>> dice = (3 * d(6) + (2 * d(4) + 5) + 3)
        >>> dict(dice.dice), dice.constant
        ({6: 3, 4: 2}, 8)
        """
        if isinstance(other, int):
            return Dice(dice=self.dice, constant=self.constant + other)
        elif isinstance(other, str):
            return self.add(Dice.from_string(other))
        elif isinstance(other, Dice):
            return self.add(other)
        else:
            raise NotImplementedError

    def __radd__(self, other) -> 'Dice':
        """
        >>> (3 + 1 * d(4)).constant
        3
        """
        if isinstance(other, int):
            return Dice(dice=self.dice, constant=self.constant + other)
        else:
            raise NotImplementedError

    def __int__(self):
        return self.result()

    def add(self, other: 'Dice'):
        return Dice(
            dice=self.dice + other.dice,
            constant=self.constant + other.constant
        )

    def roll(self) -> 'Roll':
        """
        Roll the dice, returning a wrapped result.

        >>> r = (3 * d(6) + 2).roll()
        >>> len(r.rolls[6])
        3

        >>> r = (100 * d(6)).roll()
        >>> min(r.rolls[6]), max(r.rolls[6])
        (1, 6)
        """
        rolls = {
            dice_size: [random.randint(1, dice_size) for _ in range(n)]
            for (dice_size, n) in self.dice.items()
        }
        return Roll(rolls, self.constant)

    def result(self) -> int:
        """
        Roll the result and sum to an integer.
        """
        return self.roll().total


class Roll:
    def __init__(self, rolls: Dict[int, List[int]], constant: int):
        """Wrapper for the outcome of a specific dice roll."""

        assert rolls or constant, 'Roll should have at least one dice or constant term'
        assert all([len(v) > 0 for v in rolls.values()]), 'Cannot have an empty roll for a dice size'
        self.rolls = rolls
        self.constant = constant

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.rolls}, {self.constant})'

    def __str__(self) -> str:
        return f'{self.__class__.__name__}({self.pretty(1)})'

    def __int__(self):
        return self.total

    @property
    def total(self):
        return sum(sum(result) for result in self.rolls.values()) + self.constant

    @property
    def dice(self):
        counter = Counter({
            dice_size: len(rolls_for_size)
            for dice_size, rolls_for_size in self.rolls
        })
        return Dice(dice=counter, constant=self.constant)

    def pretty(self, verbose=0) -> str:
        """
        Various pretty-print implementations.

        TODO: handle large numbers.

        >>> r = Roll({6: [1, 2, 3], 20: [8, 9]}, 12)
        >>> print(r.pretty(verbose=0))
        35

        >>> print(r.pretty(verbose=1))
        35 = 8 + 9 + 1 + 2 + 3 + 12

        >>> print(Roll({6: [1, 2, 3], 20: [8, 9]}, 12).pretty(verbose=2))
             2d20 : 17  = 8 + 9
         +    3d6 : 6   = 1 + 2 + 3
         +     12 : 12
        ---------------
         =          35
        """
        if verbose == 0:
            return str(self.total)
        elif verbose == 1:
            return '{} = {}'.format(
                self.total,
                ' + '.join([
                    str(n)
                    for (_, results) in sorted(self.rolls.items(), reverse=True)
                    for n in results
                ] + [
                    str(self.constant)
                ])
            )
        elif verbose == 2:
            parts = []
            if self.rolls:
                parts.extend([
                    (
                        f'{len(rolls)}d{dice_size}',
                        str(sum(rolls)),
                        f" = {' + '.join(str(r) for r in rolls)}"
                    )
                    for (dice_size, rolls) in sorted(self.rolls.items(), reverse=True)
                ])

            if self.constant:
                parts.append((self.constant, self.constant, ''))

            lines = [
                f' {"+" if i > 0 else " "} {term:>6} : {total:<3}{explanation}'.rstrip()
                for i, (term, total, explanation) in enumerate(parts)
            ]

            lines.append('---------------')
            lines.append(f' =          {self.total}')
            return '\n'.join(lines)


def roll(dice: Union[Dice, str]) -> int:
    """
    roll(2d(6) + 1d(10))
    """
    if isinstance(dice, Dice):
        return dice.result()
    elif isinstance(dice, str):
        return Dice.from_string(dice).result()
    else:
        raise NotImplementedError


d = Dice.one

d4 = d(4)
d6 = d(6)
d8 = d(8)
d10 = d(10)
d12 = d(12)
d20 = d(20)
d100 = d(100)
