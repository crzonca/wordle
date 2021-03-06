import itertools
import math
import re

import pandas as pd


def nerdle(first_guess='2*4+5=13',
           first_pattern=None,
           second_guess=None,
           second_pattern=None,
           third_guess=None,
           third_pattern=None,
           fourth_guess=None,
           fourth_pattern=None,
           fifth_guess=None,
           fifth_pattern=None,
           verbose=False):
    # The list of all possible 5 letter words
    possible_words = list(pd.read_csv('C:\\Users\\colin\\OneDrive\\Desktop\\nerdle.csv',
                                      header=None).squeeze())

    yellow_dict = {letter: 0 for letter in list('0123456789+-*/=')}
    if first_guess:
        possible_words, yellow_dict = get_possible_words(possible_words, first_guess, first_pattern, yellow_dict,
                                                         verbose=verbose)
    if second_guess:
        possible_words, yellow_dict = get_possible_words(possible_words, second_guess, second_pattern, yellow_dict,
                                                         verbose=verbose)
    if third_guess:
        possible_words, yellow_dict = get_possible_words(possible_words, third_guess, third_pattern, yellow_dict,
                                                         verbose=verbose)
    if fourth_guess:
        possible_words, yellow_dict = get_possible_words(possible_words, fourth_guess, fourth_pattern, yellow_dict,
                                                         verbose=verbose)
    if fifth_guess:
        possible_words, yellow_dict = get_possible_words(possible_words, fifth_guess, fifth_pattern, yellow_dict,
                                                         verbose=verbose)

    print(len(possible_words), 'Possible Words Remaining')
    entropies = get_entropies(possible_words, verbose=verbose)

    # Print the 25 most useful words
    print('Most Useful Words:')
    for word, entropy in list(entropies['entropy'].iteritems())[:25]:
        print(word, round(entropy, 3))
    print()

    # Print the 25 least useful words
    if len(possible_words) >= 50:
        print('Least Useful Words:')
        for word, entropy in list(entropies['entropy'].iteritems())[-25:]:
            print(word, round(entropy, 3))
        print()


def get_possible_words(all_words, guess, pattern, yellow_dict, verbose=False):
    result = list(zip(guess, pattern))

    green_letters = [letter for letter, key in result if key == 'G']
    yellow_letters = [letter for letter, key in result if key == 'y']
    grey_letters = [letter for letter, key in result if key == 'g']

    # We know the letters that are green are in that exact position
    # Letters that are any other color can be anything but that letter
    green_regex = [letter if key == 'G' else '[^' + letter + ']' for letter, key in result]
    green_regex = '^' + ''.join(green_regex) + '$'
    green_regex = green_regex.replace('+', '\\+')
    green_regex = green_regex.replace('*', '\\*')
    r = re.compile(green_regex)
    possible_words = list(filter(r.match, all_words))
    if verbose:
        print('Finding words matching regex:', green_regex)
        print(len(possible_words), 'words found')

    # We know that for each yellow letter, there is at least that many of them in the word
    # For example, a yellow S in a single guess means there is at least 1 S
    # Two yellow P's in a single guess means there is at least 2 P's
    yellow_dict = {letter: max(yellow_letters.count(letter) + green_letters.count(letter), count)
                   for letter, count in yellow_dict.items()}
    possible_words = [word for word in possible_words if all(word.count(letter) >= yellow_dict.get(letter)
                                                             for letter in set(yellow_dict.keys()))]
    if verbose:
        print('Finding words containing all of:', ''.join([letter * count for letter, count in yellow_dict.items()]))
        print(len(possible_words), 'words found')

    # We know the letters that are grey are not in the word, if they are not also green or yellow
    # Therefore words that contain grey letters, that are only grey, are not possible
    # Furthermore, if the letter is also green or yellow in a guess, we know there are exactly that many in the word
    possible_words = [word for word in possible_words if all(word.count(letter) ==
                                                             green_letters.count(letter) +
                                                             yellow_letters.count(letter)
                                                             for letter in set(grey_letters))]
    if verbose:
        print('Finding words that do not contain any of:', set(grey_letters) - set(green_letters) - set(yellow_letters))
        print(len(possible_words), 'words found')

    return possible_words, yellow_dict


def get_entropies(words, verbose=False):
    lookup = pd.DataFrame(index=words,
                          columns=[''.join(pattern) for pattern in itertools.product(['g', 'y', 'G'], repeat=5)] +
                                  ['entropy'])

    for num, word in enumerate(words):
        if verbose:
            print(word)
        if num % 1000 == 0 and len(words) > 1000:
            print(num)
        possible_probabilities = list()

        # combo_dict = dict()
        for letter_combo in itertools.product(['g', 'y', 'G'], repeat=8):
            # Duplicate letters cannot have the grey letter come before the yellow letter
            potential_result = list(zip(word, letter_combo))

            yellow_letters = {letter for letter, key in potential_result if key == 'y'}
            grey_letters = {letter for letter, key in potential_result if key == 'g'}
            both = yellow_letters.intersection(grey_letters)
            if both:
                if any(potential_result.index((letter, 'g')) <
                       7 - list(reversed(potential_result)).index((letter, 'y')) for letter in both):
                    possible_probabilities.append(0)
                    continue

            # Get all possible words for a given guess and pattern
            yellow_dict = {letter: 0 for letter in list('0123456789+-*/=')}
            possible_words, yellow_dict = get_possible_words(words, word, letter_combo, yellow_dict, verbose=verbose)

            probability = len(possible_words) / len(words)
            if verbose:
                print(len(possible_words), 'out of a possible', len(words),
                      'words match the pattern', letter_combo, '(' + str(round(100 * probability, 2)) + '%)')
                print()

            possible_probabilities.append(probability)
            lookup.at[word, ''.join(letter_combo)] = probability
            # combo_dict[''.join(letter_combo)] = probability

        # Using all the possible probabilities of all possible outcomes, get the entropy of the word
        entropy = get_entropy(possible_probabilities, verbose=verbose)
        lookup.at[word, 'entropy'] = entropy

        # Sort the remaining words by the amount of information they give
        lookup = lookup.sort_values(by='entropy', ascending=False)

        if verbose:
            print()

    return lookup


def get_entropy(probabilities, verbose=False):
    probabilities = [prob for prob in probabilities if prob > 0]
    if verbose:
        print(len(probabilities), 'nonzero probabilities')
        print(sum(probabilities))
    if abs(sum(probabilities) - 1) > 1e-6:
        print(round(sum(probabilities), 3), 'is not 1')

    entropy = sum([probability * math.log(1 / probability, 2) for probability in probabilities])
    if verbose:
        for probability in probabilities:
            print(round(probability, 3), '*',
                  round(math.log(1 / probability, 2), 3), '=',
                  round(probability * math.log(1 / probability, 2), 3))
        print('total entropy:', round(entropy, 3))

    if entropy > math.log(6561, 2):
        print('Impossible Entropy')

    return entropy


def create_equation_set():
    numbers = list('0123456789')
    operators = list('+-*/')
    valid_equations = list()
    for three_digit_solution in itertools.product(numbers, repeat=3):
        if three_digit_solution[0] == '0':
            continue
        three_digit_solution = ''.join(three_digit_solution)
        for two_digit in itertools.product(numbers, repeat=2):
            if two_digit[0] == '0':
                continue
            two_digit = ''.join(two_digit)
            for one_digit in numbers:
                try:
                    if eval(two_digit + '*' + one_digit + '==' + three_digit_solution):
                        valid_equations.append(two_digit + '*' + one_digit + '=' + three_digit_solution)
                    if eval(two_digit + '+' + one_digit + '==' + three_digit_solution):
                        valid_equations.append(two_digit + '+' + one_digit + '=' + three_digit_solution)
                except (SyntaxError, ZeroDivisionError) as e:
                    i = 0
    for two_digit_solution in itertools.product(numbers, repeat=2):
        if two_digit_solution[0] == '0':
            continue
        two_digit_solution = ''.join(two_digit_solution)
        for first_two in itertools.product(numbers, repeat=2):
            if first_two[0] == '0':
                continue
            first_two = ''.join(first_two)
            for second_two in itertools.product(numbers, repeat=2):
                if second_two[0] == '0':
                    continue
                second_two = ''.join(second_two)
                try:
                    if eval(first_two + '+' + second_two + '==' + two_digit_solution):
                        valid_equations.append(first_two + '+' + second_two + '=' + two_digit_solution)
                    if eval(first_two + '-' + second_two + '==' + two_digit_solution):
                        valid_equations.append(first_two + '-' + second_two + '=' + two_digit_solution)
                except (SyntaxError, ZeroDivisionError) as e:
                    i = 0
        for three_digit in itertools.product(numbers, repeat=3):
            if three_digit[0] == '0':
                continue
            three_digit = ''.join(three_digit)
            for one_digit in numbers:
                try:
                    if eval(three_digit + '/' + one_digit + '==' + two_digit_solution):
                        valid_equations.append(three_digit + '/' + one_digit + '=' + two_digit_solution)
                    if eval(three_digit + '-' + one_digit + '==' + two_digit_solution):
                        valid_equations.append(three_digit + '-' + one_digit + '=' + two_digit_solution)
                except (SyntaxError, ZeroDivisionError) as e:
                    i = 0
        for first_one in numbers:
            for second_one in numbers:
                for third_one in numbers:
                    for ops in itertools.permutations(operators, 2):
                        operator1 = ops[0]
                        operator2 = ops[1]
                        try:
                            if eval(first_one + operator1 + second_one + operator2 + third_one +
                                    '==' + two_digit_solution):
                                valid_equations.append(first_one + operator1 + second_one + operator2 + third_one +
                                                       '=' + two_digit_solution)
                        except (SyntaxError, ZeroDivisionError) as e:
                            i = 0
    for one_digit_solution in numbers:
        one_digit_solution = str(one_digit_solution)
        for three_digit in itertools.product(numbers, repeat=3):
            if three_digit[0] == '0':
                continue
            three_digit = ''.join(three_digit)
            for two_digit in itertools.product(numbers, repeat=2):
                if two_digit[0] == '0':
                    continue
                two_digit = ''.join(two_digit)
                try:
                    if eval(three_digit + '-' + two_digit + '==' + one_digit_solution):
                        valid_equations.append(three_digit + '-' + two_digit + '=' + one_digit_solution)
                    if eval(three_digit + '/' + two_digit + '==' + one_digit_solution):
                        valid_equations.append(three_digit + '/' + two_digit + '=' + one_digit_solution)
                except (SyntaxError, ZeroDivisionError) as e:
                    i = 0
        for two_digit in itertools.product(numbers, repeat=2):
            if two_digit[0] == '0':
                continue
            two_digit = ''.join(two_digit)
            for first_one in numbers:
                for second_one in numbers:
                    for ops in itertools.permutations(operators, 2):
                        operator1 = ops[0]
                        operator2 = ops[1]
                        first_eq = two_digit + operator1 + first_one + operator2 + second_one
                        second_eq = first_one + operator1 + two_digit + operator2 + second_one
                        third_eq = first_one + operator1 + second_one + operator2 + two_digit
                        try:
                            if eval(first_eq + '==' + one_digit_solution):
                                valid_equations.append(first_eq + '=' + one_digit_solution)
                            if eval(second_eq + '==' + one_digit_solution):
                                valid_equations.append(second_eq + '=' + one_digit_solution)
                            if eval(third_eq + '==' + one_digit_solution):
                                valid_equations.append(third_eq + '=' + one_digit_solution)
                        except (SyntaxError, ZeroDivisionError) as e:
                            i = 0

    ser = pd.Series(valid_equations)
    ser.to_csv('C:\\Users\\colin\\OneDrive\\Desktop\\nerdle.csv')