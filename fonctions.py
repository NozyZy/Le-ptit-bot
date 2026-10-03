import math
import random


# Miller-Rabin with the first 13 primes as bases is exact below this limit
# (Sorenson & Webster, 2015)
IS_PRIME_LIMIT = 3317044064679887385961981
_MR_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41)


async def is_prime(nb):
    if nb < 2:
        return False
    for p in _MR_BASES:
        if nb % p == 0:
            return nb == p
    if nb >= IS_PRIME_LIMIT:
        raise ValueError("is_prime is only exact below IS_PRIME_LIMIT")

    d, s = nb - 1, 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in _MR_BASES:
        x = pow(a, d, nb)
        if x in (1, nb - 1):
            continue
        for _ in range(s - 1):
            x = pow(x, 2, nb)
            if x == nb - 1:
                break
        else:
            return False
    return True


def findAndReplace(letter, dico):
    reponse = "00"
    exceptions = ["y", "u", "n", "m", "i"]
    while reponse[0] != letter or reponse[1] in exceptions:
        reponse = random.choice(dico)
    reponse = reponse.replace(reponse[0], "", 1)
    return reponse


def equal_games(liste):
    # Il vaut mieux que la liste soit déjà mélangée, mais on peut le faire ici aussi.
    # Le programme renvoie une liste 2D composant les équipes

    tailleListe = len(liste)
    tailleMin, tailleMax = 5, 10
    tailleEquip = []
    nbEquip = 0
    equip = []

    for i in range(tailleMax, tailleMin, -1):
        if tailleListe % i == 0:
            nbEquip = tailleListe // i
            for _ in range(nbEquip):
                tailleEquip.append(i)
            break
        elif tailleListe % i == 1 and i < tailleMax:
            nbEquip = tailleListe // i
            for j in range(nbEquip):
                if j == 0:
                    tailleEquip.append(i + 1)
                else:
                    tailleEquip.append(i)
            break

    if nbEquip == 0:
        tailleEquip.append(tailleMax)
        while tailleListe > 0 and tailleMin < tailleEquip[0] and nbEquip < 8:
            tailleListe -= tailleEquip[0]
            nbEquip += 1

            if 0 < tailleListe < tailleMin and nbEquip < 8:
                tailleEquip[0] -= 1
                tailleListe = len(liste)
                nbEquip = 0

        for i in range(1, nbEquip):
            tailleEquip.append(tailleEquip[0])

    j = 0
    for i in range(nbEquip):
        list1 = []
        for _ in range(tailleEquip[i]):
            if j < len(liste):
                list1.append(liste[j])
                j += 1
        equip.append(list1)
    return equip


def facto(n):
    return math.factorial(n)


def strToInt(list):
    nb = 0
    for j in range(len(list)):
        nb += (ord(list[j]) - 48) * 10**(len(list) - j - 1)
    return nb


def verifAlphabet(string):
    string = string.lower()
    for i in range(len(string)):
        if (i + 3 <= len(string) and len(string) >= 3 and
            (string[i] == string[i + 1] and string[i] == string[i + 2])):
            return False
        if (ord(string[i]) < 97 or 97 + 26 < ord(string[i]) and string[i]
                not in ["é", "è", "à", "ï", "ø", "â", "ñ", "î", "û", "ç"]):
            return False
    return True


def crypting(string):
    encrypted = string
    decrypted = ""
    for j in range(1, 26):
        for i in encrypted:
            if ord(i) < 97 or ord(i) > 97 + 26:
                pass
            elif ord(i) + j >= 97 + 26:
                decrypted += chr(ord(i) + j - 26)
            else:
                decrypted += chr(ord(i) + j)
        decrypted += " / "
    return str(decrypted)


def nbInStr(Message, start, end):
    i = start
    list = []
    while i < end:
        if 48 <= ord(Message[i]) <= 57:
            list.append(Message[i])
        i += 1
    return list
