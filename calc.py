from typing import Union, Tuple
import re


def evaluate(sentence_in: str) -> Union[str, int, float]:
    if sentence_in.count('(') != sentence_in.count(')'):
        raise UnpairedBrackets(sentence_in)
    sentence = sentence_in.replace(' ', '')
    sentence = sentence.replace('**', '^')
    try:
        sentence = _deal_with_brackets(sentence)
        sentence = _check_for_signs(sentence)
    except ZeroDivisionError:
        raise ZeroDivision(sentence)
    return _format(sentence)


signs = ['+', '-', '*', '/', '^', '%']
rs = '\\' + '\\'.join(signs)
regular = re.compile(rf'([^{rs}]+)([{rs}])(-?[^{rs}]+)')
hp_regular = re.compile(rf'([^{rs}]+)([\*\/\%])(-?[^{rs}]+)')
expon_regular = re.compile(rf'([^{rs}]+)([\^])(-?[^{rs}]+)')

base_signs = {
    '+': float.__add__,
    '-': float.__sub__,
    '*': float.__mul__,
    '/': float.__truediv__,
    '%': float.__mod__
}


def _isdigit(string: str) -> bool:
    try:
        float(string)
        return True
    except ValueError:
        return False


def _calc(sentence: str, exp: Tuple[str, str, str] = None) -> str:
    if exp is None:
        exp = regular.findall(sentence)
    if not exp:
        return sentence
    first, sign, second = tuple(exp[0])
    if not _isdigit(first) or not _isdigit(second):
        if sign == '+':
            return str(first) + str(second)
        else:
            return sentence
    first_f = float(first)
    second_f = float(second)
    if first_f > 1e15 or second_f > 1e15:
        raise ValueTooBig(sentence)
    if sign in base_signs:
        return str(base_signs.get(sign)(first_f, second_f))
    elif sign == '^':
        if second_f < 1:
            raise ExponentError(sentence)
        return str(_exponent(first_f, int(second_f)))


def _exponent(base: float, exponent: int) -> float:
    result = base
    for _ in range(exponent-1):
        result = result * base
        if result > 1e15:
            raise ValueTooBig(f"{result}*{base}")
    return result


_last_exp = []


def _check_for_signs(sentence: str) -> str:
    global _last_exp
    for sign in signs:
        if sign in sentence:
            if 'e+' in sentence:
                sentence = sentence.replace('e+', 'e')
            if sign in {'+', '-'} and _hp_signs_in(sentence):
                exp = hp_regular.findall(sentence)
            elif sign in {'+', '-', '/', '*', '%'} and '^' in sentence:
                exp = expon_regular.findall(sentence)
            else:
                exp = regular.findall(sentence)
            if not exp or exp == _last_exp:  # noqa
                return sentence
            _last_exp = exp
            to_replace = ''.join(exp[0])
            sentence = sentence.replace(to_replace, _calc(sentence, exp))
            return _check_for_signs(sentence)
    return sentence


def _hp_signs_in(sentence: str) -> bool:
    for sign in ['*', '/', '^', '%']:
        if sign in sentence:
            return True
    return False


def _deal_with_brackets(sentence: str) -> str:
    operation = ''
    for char in sentence:
        if char == '(':
            operation = ''
            continue
        if char == ')':
            sentence = sentence.replace('('+operation+')', _check_for_signs(operation)) # noqa
            operation = ''
            return _deal_with_brackets(sentence)
        operation += char
    return sentence


def _format(text: str) -> str:  # noqa (but i agree, really too complex)
    if '.' not in text:
        return text
    dot_splitted = text.split('.')
    if len(dot_splitted) > 2:
        return text
    integer, after_dot = dot_splitted[0], dot_splitted[1]
    if not integer.isdigit:
        return text
    e_splitted = after_dot.split('e')
    if len(e_splitted) > 2:
        return text
    elif 'e' not in after_dot:
        if '999' in text or '000' in text:
            try:
                number = float(text)
            except ValueError:
                return text
            if number > 1 or number < -1:
                return round(number, 3)
            else:
                return _format_fraction(text)
        return text
    fraction, multiplier = e_splitted[0], e_splitted[1]
    if not fraction.isdigit() or not _isdigit(multiplier):
        return text
    multiplier = int(multiplier)
    if multiplier > 0:
        return integer + fraction + '0'*(multiplier - len(fraction))
    else:
        result = '0.'+'0'*multiplier + integer + fraction
        return _format_fraction(result)


def _format_fraction(text: str) -> str:
    for i, char in enumerate(text[::-1]):
        if i == 0: continue  # noqa
        if char not in {'9', '0'}: break  # noqa
    if text[-i] == '9':
        return text[:-i-1] + str(int(text[-i-1])+1)
    return text[:-i]


class CalcError(Exception):
    sentence: str

    def __init__(self, sentence):
        self.sentence = sentence


class UnpairedBrackets(CalcError):
    def __init__(self, sentence):
        super().__init__(sentence)


class ValueTooBig(CalcError):
    def __init__(self, sentence):
        super().__init__(sentence)


class ZeroDivision(CalcError):
    def __init__(self, sentence):
        super().__init__(sentence)


# fractional and negative exponents not implemented (but only negative raises)
class ExponentError(CalcError):
    def __init__(self, sentence):
        super().__init__(sentence)


if __name__ == '__main__':
    import traceback
    while True:
        try:
            text = input("Input expression: ")
            print("Response:", evaluate(text))
        except CalcError as e:
            print(f"Calculating error: {e.__class__.__name__}, {e.sentence}")
        except Exception:
            print(traceback.format_exc())
