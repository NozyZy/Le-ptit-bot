import random


def addition(a, b):
    return a + b


def soustraction(a, b):
    return a - b


def multiplication(a, b):
    return a * b


def division(a, b):
    if b == 0:
        print("ERREUR - Division par 0")
    else:
        return a / b


def is_prime(nb):
    print(nb)
    if nb <= 3:
        return nb > 1
    elif nb % 2 == 0 or nb % 3 == 0:
        return False

    i = 5

    while i * i <= nb:
        if nb % i == 0 or nb % (i + 2) == 0:
            return False
        i = i + 6
    return True


def finndAndReplace(letter, dico):
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
    if n == 0:
        return 1
    return n * facto(n - 1)


def strToInt(list):
    nb = 0
    for j in range(len(list)):
        nb += (ord(list[j]) - 48) * 10**(len(list) - j - 1)
    return nb


def state_alpha(ch1, ch2):
    if ord(ch1) < ord(ch2):
        return 1
    elif ord(ch1) == ord(ch2):
        return 0
    else:
        return -1


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


def verifNoNb(string):
    string = string.lower()
    for i in string:
        if 48 <= ord(i) <= 48 + 9:
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


abscisse = {
    "A": 0,
    "B": 1,
    "C": 2,
    "D": 3,
    "E": 4,
    "F": 5,
    "G": 6,
    "H": 7,
    "I": 8,
    "J": 9,
    "K": 10,
    "L": 11,
    "M": 12,
    "N": 13,
    "O": 14,
    "P": 15,
    "Q": 16,
    "R": 17,
    "S": 18,
    "T": 19,
    "U": 20,
    "V": 21,
    "W": 22,
    "X": 23,
    "Y": 24,
    "Z": 25,
}


def init_plateau():
    grille = []
    a = 8
    for i in range(a + 1):
        grille.append([" ."] * (a + 1))
    return grille


def init_position(grille):
    if (len(grille) - 1) % 2 == 0:
        milieu_g_b = (len(grille) - 2) // 2
        milieu_d_h = (len(grille) - 1) // 2
    else:
        milieu_g_b = (len(grille) - 1) // 2
        milieu_d_h = len(grille) // 2
    grille[milieu_g_b][milieu_d_h] = "X"
    grille[milieu_d_h][milieu_g_b] = "X"
    grille[milieu_g_b][milieu_g_b] = "O"
    grille[milieu_d_h][milieu_d_h] = "O"

    return grille


def saisi_position(grille, tour):
    if (tour % 2 == 0
        ):  # sera pair pour le joueur 1 Noir, et impair pour le joueur 2 Blanc
        joueur = 1
        caractere = " O"
        inv_caractere = " X"
    else:
        joueur = 2
        caractere = " X"
        inv_caractere = " O"
    # coups possibles de ce tour
    coups_possibles = verif_coup(grille, caractere, inv_caractere)
    # coups possibles du prochain tour
    coups_possibles_inverse = verif_coup(grille, inv_caractere, caractere)
    if (len(coups_possibles) == 0 and len(coups_possibles_inverse) == 0
        ):  # s'il n'y a pas de coups à ce tour et au tour prochain, fin de jeu
        print("Aucun coups possible.", end="")
        return arreter_partie()  # return True
    else:
        saisi = str(input(f" - Joueur {joueur}, à vous de choisir : "))
        saisi = saisi.lower()
        saisi = saisi.replace(" ", "")
        if saisi == "stop" or saisi == "Stop" or saisi == "STOP":
            return arreter_partie()  # return True
        # si le jour ne passe pas son tour, il peut jouer
        if passe_tour(coups_possibles) == False:
            if saisi == "c":
                liste_coups_valides(coups_possibles)
            position = str(input("Saisir les coordonées : "))
            position = position.replace(" ", "")
            position = position.upper()

            while position not in coups_possibles:  # vérifie la validité de son coup
                position = str(input("Saisir les coordonées : "))
                position = position.replace(" ", "")
                position = position.upper()
            ecrire_case(grille, position, caractere)  # écrit son coup
        else:
            # fin de tour, mais pas fin de partie (fin de partie = True)
            return False

        try:
            # test si l'abcisse est à 2 nombres (>10)
            y = int(f"{position[1]}{position[2]}") - 1
        except IndexError:
            y = int(position[1]) - 1

        # prend la lettre de la position (ex : A10 → A)
        x = int(abscisse[position[0]])
        x_cst = x
        y_cst = y
        # on va vérifier, en partant de la case écrite, tout autour si on peut faire un aller retoru entre 2 meme caracteres, ne passant que entre des caracteres inverses à retourner
        while grille[y + 1][x] == inv_caractere:  # retourne case en haut
            y += 1
        y += 1
        if grille[y][x] == caractere:
            while grille[y - 1][x] == inv_caractere:
                y += -1
                ecrire_case(grille, str(chr(65 + x)) + str(y + 1), caractere)

        y = y_cst

        while grille[y][x + 1] == inv_caractere:  # retourne case à gauche
            x += 1
        x += 1
        if grille[y][x] == caractere:
            while grille[y][x - 1] == inv_caractere:
                x += -1
                ecrire_case(grille, str(chr(65 + x)) + str(y + 1), caractere)

        x = x_cst

        while grille[y][x - 1] == inv_caractere:  # retourne case à droite
            x += -1
        x += -1
        if grille[y][x] == caractere:
            while grille[y][x + 1] == inv_caractere:
                x += 1
                ecrire_case(grille, str(chr(65 + x)) + str(y + 1), caractere)

        x = x_cst
        while grille[y - 1][x] == inv_caractere:  # retourne case en bas
            y += -1
        y += -1
        if grille[y][x] == caractere:
            while grille[y + 1][x] == inv_caractere:
                y += 1
                ecrire_case(grille, str(chr(65 + x)) + str(y + 1), caractere)

        y = y_cst

        while (grille[y - 1][x + 1] == inv_caractere
               ):  # retourne case diagonale bas gauche
            y += -1
            x += 1
        x += 1
        y += -1
        if grille[y][x] == caractere:
            while grille[y + 1][x - 1] == inv_caractere:
                y += 1
                x += -1
                ecrire_case(grille, str(chr(65 + x)) + str(y + 1), caractere)

        y = y_cst
        x = x_cst

        while (grille[y - 1][x - 1] == inv_caractere
               ):  # retourne case diagonale bas droite
            y += -1
            x += -1
        x += -1
        y += -1
        if grille[y][x] == caractere:
            while grille[y + 1][x + 1] == inv_caractere:
                y += 1
                x += 1
                print(str(chr(65 + x)) + str(y + 1))
                ecrire_case(grille, str(chr(65 + x)) + str(y + 1), caractere)

        y = y_cst
        x = x_cst

        while (grille[y + 1][x - 1] == inv_caractere
               ):  # retourne case diagonale haut droite
            y += 1
            x += -1
        y += 1
        x += -1
        if grille[y][x] == caractere:
            while grille[y - 1][x + 1] == inv_caractere:
                y += -1
                x += 1
                ecrire_case(grille, str(chr(65 + x)) + str(y + 1), caractere)

        y = y_cst
        x = x_cst

        while (grille[y + 1][x + 1] == inv_caractere
               ):  # retourne case diagonale haut gauche
            y += 1
            x += 1
        y += 1
        x += 1
        if grille[y][x] == caractere:
            while grille[y - 1][x - 1] == inv_caractere:
                y += -1
                x += -1
                ecrire_case(grille, str(chr(65 + x)) + str(y + 1), caractere)

        return position


def liste_sans_doublon(liste):
    new_liste = []
    new_liste.append(liste[0])
    for i in range(1, len(liste)):
        double = False
        j = 1
        while j < len(new_liste) and double == False:
            if liste[i] == new_liste[j]:
                double = True
            j += 1
        if double == False and j == len(
                new_liste) and new_liste[0] != liste[i]:
            new_liste.append(liste[i])
    return new_liste


def verif_coup(grille, caractere, inv_caractere):
    all_coups = []  # liste avec toutes les position de la grille, type A00
    for i in range(0, len(grille) - 1):
        # liste 2D pour récréer la grille
        all_coups.append(["."] * (len(grille) - 1))
    coups_possibles = (
        [])  # liste contenant tous les coups jouables, en fonction du joueur
    for i in range(0, len(grille) - 1):
        val_y = i + 1  # commence à 1
        for j in range(0, len(grille) - 1):
            val_x = chr(65 + j)  # commence à A
            val = str(val_x) + str(val_y)
            all_coups[i][j] = val
    for y in range(0, len(grille) - 1):
        y_cst = y
        for x in range(0, len(grille) - 1):
            x_cst = x
            # on va vérifier, autour de chaque caractère, si on peut poser des pions pour encadrer des pions inverses
            if grille[y][x] == caractere:
                while grille[y + 1][x] == inv_caractere:  # case du dessous
                    y += 1
                if grille[y][x] == inv_caractere and grille[y + 1][x] == " .":
                    coups_possibles.append(all_coups[y + 1][x])
                y = y_cst

                while grille[y][x + 1] == inv_caractere:  # case a droite
                    x += 1
                if grille[y][x] == inv_caractere and grille[y][x + 1] == " .":
                    coups_possibles.append(all_coups[y][x + 1])

                x = x_cst

                while grille[y][x - 1] == inv_caractere:  # case a gauche
                    x += -1
                if grille[y][x] == inv_caractere and grille[y][x - 1] == " .":
                    coups_possibles.append(all_coups[y][x - 1])

                x = x_cst

                while grille[y - 1][x] == inv_caractere:  # case au dessus
                    y += -1
                if grille[y][x] == inv_caractere and grille[y - 1][x] == " .":
                    coups_possibles.append(all_coups[y - 1][x])

                y = y_cst

                while (grille[y - 1][x + 1] == inv_caractere
                       ):  # case diagonale haut droite
                    y += -1
                    x += 1
                if grille[y][x] == inv_caractere and grille[y - 1][x +
                                                                   1] == " .":
                    coups_possibles.append(all_coups[y - 1][x + 1])

                y = y_cst
                x = x_cst

                while (grille[y - 1][x - 1] == inv_caractere
                       ):  # case diagonale haut gauche
                    y += -1
                    x += -1
                if grille[y][x] == inv_caractere and grille[y - 1][x -
                                                                   1] == " .":
                    coups_possibles.append(all_coups[y - 1][x - 1])

                y = y_cst
                x = x_cst

                while (grille[y + 1][x - 1] == inv_caractere
                       ):  # case diagonale bas gauche
                    y += 1
                    x += -1
                if grille[y][x] == inv_caractere and grille[y + 1][x -
                                                                   1] == " .":
                    coups_possibles.append(all_coups[y + 1][x - 1])

                y = y_cst
                x = x_cst

                while (grille[y + 1][x + 1] == inv_caractere
                       ):  # case diagonale bas droite
                    y += 1
                    x += 1
                if grille[y][x] == inv_caractere and grille[y + 1][x +
                                                                   1] == " .":
                    coups_possibles.append(all_coups[y + 1][x + 1])
                y = y_cst
                x = x_cst
    if (len(coups_possibles) !=
            0):  # si la liste n'est pas vide, on enlèves tous les doublons
        coups_possibles = liste_sans_doublon(coups_possibles)
    return coups_possibles


def liste_coups_valides(coups_possibles):
    if len(coups_possibles) != 0:
        print("Liste des coups possibles : ", end="")
        for i in coups_possibles:
            print(i, end=" ")
        print("\n", end="")


def ecrire_case(grille, position, caractere):
    try:
        grille[int(f"{position[1]}{position[2]}") - 1][abscisse[position[
            0]]] = caractere  # on test si l'ordonée est à 2 chiffres (>10)

    except IndexError:
        grille[int(position[1]) - 1][abscisse[position[0]]] = caractere
        # on transforme une coordonée de type A00 en [0,0], puis on écrit dans la case  correspondante la caractère du joueur
    finally:
        return grille


def passe_tour(coups_possibles):  # true si oui, il passe son tour
    if len(coups_possibles) == 0:  # pas de coups possibles = passe son tour
        print("Aucun coup possible. Joueur suivant. Appuyer sur Entrée")
        text = input()  # sert uniquement de pause
        return True
    return False


def arreter_partie():
    print("Fin de partie ---")
    return True


def winner(grille):
    nb_X = 0  # nombre de blanc
    nb_O = 0  # nombre de noir
    for y in range(0, len(grille) - 1):
        for x in range(0, len(grille) - 1):
            if grille[y][x] == " ♦":
                nb_X += 1
            elif grille[y][x] == " ♠":
                nb_O += 1
    print(" #", "♦ ", "= ", nb_X, "\n #", "♠ ", "= ", nb_O, sep="")
    if nb_X == nb_O:
        print("Les 2 joueurs gagnent,", "égalité !")
    elif nb_O > nb_X:
        print("Le joueur", " noir ", "gagne !", sep="")
    else:
        print("Le joueur", " rouge ", "gagne !", sep="")
