import itertools
import math
import re

import pandas as pd


def wordle(first_guess='tares',
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
    possible_words = list(pd.read_csv('words.csv', header=None).squeeze())

    yellow_dict = {letter: 0 for letter in list('abcdefghijklmnopqrstuvwxyz')}
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

    # Sort the remaining words by the amount of information they give
    entropies = get_entropies(possible_words, verbose=verbose)
    entropies = {k: v for k, v in sorted(entropies.items(), key=lambda item: item[1], reverse=True)}

    # Print the 25 most useful words
    print('Most Useful Words:')
    for word, entropy in list(entropies.items())[:25]:
        print(word, round(entropy, 3))
    print()

    # Print the 25 least useful words
    if len(possible_words) >= 50:
        print('Least Useful Words:')
        for word, entropy in list(entropies.items())[-25:]:
            print(word, round(entropy, 3))
        print()


def get_possible_words(all_words, guess, pattern, yellow_dict, verbose=False):
    result = list(zip(guess, pattern))

    green_regex = [letter if key == 'G' else '.' for letter, key in result]
    green_regex = '^' + ''.join(green_regex) + '$'
    r = re.compile(green_regex)
    possible_words = list(filter(r.match, all_words))
    if verbose:
        print('Finding words matching regex:', green_regex)
        print(len(possible_words), 'words found')

    yellow_regex = ['[^' + letter + ']' if key == 'y' else '.' for letter, key in result]
    yellow_regex = '^' + ''.join(yellow_regex) + '$'
    r = re.compile(yellow_regex)
    possible_words = list(filter(r.match, possible_words))
    if verbose:
        print('Finding words matching regex:', yellow_regex)
        print(len(possible_words), 'words found')

    yellow_letters = [letter for letter, key in result if key == 'y']
    yellow_dict = {letter: max(yellow_letters.count(letter), count) for letter, count in yellow_dict.items()}
    possible_words = [word for word in possible_words if all(yellow_dict.get(required_letter) <=
                                                             word.count(required_letter)
                                                             for required_letter in set(yellow_dict.keys()))]
    if verbose:
        print('Finding words containing all of:', ''.join([letter * count for letter, count in yellow_dict.items()]))
        print(len(possible_words), 'words found')

    grey_letters = [letter for letter, key in result if key == 'g']
    impossible_words = [word for word in possible_words if any(letter in word for letter in grey_letters)]
    possible_words = list(set(possible_words) - set(impossible_words))
    if verbose:
        print('Finding words that do not contain any of:', grey_letters)
        print(len(possible_words), 'words found')

    return possible_words, yellow_dict


def get_entropies(words, verbose=False):
    entropies = dict()

    for num, word in enumerate(words):
        if verbose:
            print(word)
        if num % 1000 == 0 and len(words) > 1000:
            print(num)
        possible_probabilities = list()

        for letter_combo in itertools.product(['g', 'y', 'G'], repeat=5):
            yellow_dict = {letter: 0 for letter in list('abcdefghijklmnopqrstuvwxyz')}
            possible_words, yellow_dict = get_possible_words(words, word, letter_combo, yellow_dict, verbose=verbose)

            probability = len(possible_words) / len(words)
            if verbose:
                print(len(possible_words), 'out of a possible', len(words),
                      'words match the pattern', letter_combo, '(' + str(round(100 * probability, 2)) + '%)')
                print()

            possible_probabilities.append(probability)

        # Using all the possible probabilities of all possible outcomes, get the entropy of the word
        entropies[word] = get_entropy(possible_probabilities, verbose=verbose)

        if verbose:
            print()

    return entropies


def get_entropy(probabilities, verbose=False):
    probabilities = [prob for prob in probabilities if prob > 0]
    if verbose:
        print(len(probabilities), 'nonzero probabilities')
        print(sum(probabilities))

    entropy = sum([probability * math.log(1 / probability, 2) for probability in probabilities])
    if verbose:
        for probability in probabilities:
            print(round(probability, 3),
                  '*',
                  round(math.log(1 / probability, 2), 3),
                  '=',
                  round(probability * math.log(1 / probability, 2), 3))
        print('total entropy:', round(entropy, 3))

    if entropy > math.log(243, 2):
        print('Impossible Entropy')

    return entropy
