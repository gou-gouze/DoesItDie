"""Runs real WoW: Forever FRENCH tooltips through the addon's French parser (DoesItDie/Locale.lua) plus the
real English-keyed tables from DoesItDie.lua, and checks what the addon would track.

This is the French counterpart of test_parse.py / test_spellbook.py. Every description below is the actual
French `.q` tooltip text served by Wowhead for WoW: Forever (data env Forever, locale fr); the expectation is
what the English build produces for the same wording, so a regression in the French grammar shows up here.

    pip install lupa
    python tools/test_locale_fr.py
"""
import os
import sys
from lupa import LuaRuntime

HERE = os.path.dirname(os.path.abspath(__file__))
ADDON = os.path.join(HERE, "..", "DoesItDie")
main_src = open(os.path.join(ADDON, "DoesItDie.lua"), encoding="utf-8").read()
locale_src = open(os.path.join(ADDON, "Locale.lua"), encoding="utf-8").read()


def chunk(start_marker, end_marker):
    start = main_src.index(start_marker)
    return main_src[start:main_src.index(end_marker, start)]


lua = LuaRuntime(unpack_returned_tuples=True)
G = lua.globals()

# 1. Load Locale.lua as frFR so it installs ns.parser (French) and ns.canonicalName (French name -> English).
G.GetLocale = lua.eval('function() return "frFR" end')
ns = lua.table()
lua.eval("load")(locale_src, "Locale")("DoesItDie", ns)
assert ns.parser is not None, "Locale.lua did not install a French parser"
G.L = ns.parser
G.canon = ns.canonicalName

# 2. Build the real tables + parseDot from DoesItDie.lua (parseDot defers to the global L when set), then a
#    tracker that mirrors onPlayerCast's decision (canon the name, ignore list, parse, interval, school).
track = lua.execute("\n".join([
    "local function isSecret(v) return false end",
    chunk("local DEFAULT_TICK_INTERVAL", "local TICK_MATCH_WINDOW"),
    chunk("-- Tick intervals that differ", "-- User options"),
    chunk("local function schoolFromWords",
          "---------------------------------------------------------------------------\n-- DoT tracking"),
    """
    return function(name, desc, comboPoints)
        local cname = canon(name)
        if IGNORED_SPELLS[cname] then return "ignored (list)" end
        local total, school, duration, stated = parseDot(desc, comboPoints)
        if not total then return "not tracked" end
        local interval = stated or KNOWN_TICK_INTERVALS[cname] or DEFAULT_TICK_INTERVAL
        school = SCHOOL_BY_NAME[cname] or school
        local ticks = math.max(1, math.floor(duration / interval + 0.5))
        return string.format("%d dmg, school %d, %gs, every %gs -> %d ticks of %.1f",
            total, school, duration, interval, ticks, total / ticks)
    end
    """,
]))

# (French spell name, French tooltip text, combo points or None, expected tracking result)
CASES = [
    # --- tracked DoTs, every school and clause shape ---
    ("Corruption", "Corrompt la cible et lui inflige 40 points de dégâts d'Ombre en 12 sec.",
     None, "40 dmg, school 32, 12s, every 3s -> 4 ticks of 10.0"),
    ("Éclat lunaire", "Brûle l'ennemi et lui inflige 10 à 12 points de dégâts des Arcanes, puis 12 points de dégâts des Arcanes supplémentaires en 9 sec.",
     None, "12 dmg, school 64, 9s, every 3s -> 3 ticks of 4.0"),
    ("Mot de l'ombre : Douleur", "Un mot des ténèbres qui inflige 30 points de dégâts d'Ombre en 18 sec.",
     None, "30 dmg, school 32, 18s, every 3s -> 6 ticks of 5.0"),
    ("Peste dévorante", "La cible contracte une maladie qui lui inflige 128 points de dégâts d'Ombre en 24 sec. Les dégâts infligés par la Peste dévorante soignent le lanceur de sorts.",
     None, "128 dmg, school 32, 24s, every 3s -> 8 ticks of 16.0"),
    ("Morsure de serpent", "Mord la cible et lui inflige 10 points de dégâts de Nature en 15 sec. Une seule technique de Morsure ou de Piqûre peut être active sur la cible par chasseur.",
     None, "10 dmg, school 8, 15s, every 3s -> 5 ticks of 2.0"),
    ("Sarments", "Immobilise la cible sur place et lui inflige 20 points de dégâts de nature en 12 sec. Si la cible subit des dégâts, l'effet peut être interrompu.",
     None, "20 dmg, school 8, 12s, every 3s -> 4 ticks of 5.0"),
    ("Boule de feu", "Projette une boule ardente qui inflige 15 à 23 points de dégâts de Feu et 2 points de dégâts de Feu supplémentaires en 4 sec.",
     None, "2 dmg, school 4, 4s, every 2s -> 2 ticks of 1.0"),
    ("Explosion pyrotechnique", "Lance un immense rocher enflammé qui inflige 101 à 131 points de dégâts de Feu et 44 points de dégâts de Feu supplémentaires en 12 sec.",
     None, "44 dmg, school 4, 12s, every 3s -> 4 ticks of 11.0"),
    ("Flammes sacrées", "Consume l'ennemi dans des flammes sacrées et lui inflige 53 à 65 points de dégâts du Sacré et 20 points de dégâts du Sacré supplémentaires en 10 sec.",
     None, "20 dmg, school 2, 10s, every 2s -> 5 ticks of 4.0"),
    ("Plaie d'agonie", "Afflige la cible d'une plaie d'agonie qui lui inflige 72 points de dégâts d'ombre en 24 sec. Les dégâts sont progressifs et sont plus importants avec le temps.",
     None, "72 dmg, school 32, 24s, every 2s -> 12 ticks of 6.0"),
    # --- Physical bleeds: "points de dégâts" with no school, and "perd ... points de vie" ---
    ("Garrot", "Garrotte l'ennemi et lui inflige 144 points de dégâts en 18 sec, augmentés par votre puissance d'attaque. Il faut être camouflé et derrière la cible. Vous gagnez 1 point de combo.",
     None, "144 dmg, school 1, 18s, every 3s -> 6 ticks of 24.0"),
    ("Griffure", "Lacère la cible, lui infligeant 23 points de dégâts et 48 points de dégâts supplémentaires sur la durée en 9 sec. Vous gagnez 1 point de combo.",
     None, "48 dmg, school 1, 9s, every 3s -> 3 ticks of 16.0"),
    ("Traquenard", "Attaque la cible par surprise et l'étourdit pendant 2 sec en lui infligeant 90 points de dégâts en 18 sec. Vous devez être camouflé et derrière la cible. Vous gagnez 1 point de combo.",
     None, "90 dmg, school 1, 18s, every 3s -> 6 ticks of 15.0"),
    ("Pourfendre", "Blesse la cible. Elle saigne et perd 15 points de vie en 9 sec.",
     None, "15 dmg, school 1, 9s, every 3s -> 3 ticks of 5.0"),
    # --- health-drain rate (Siphon Life): school comes from SCHOOL_BY_NAME, not the text ---
    ("Siphon de vie", "Transfère 11 points de vie de la cible vers le lanceur ou la lanceuse toutes les 3 s. Dure 30 sec.",
     None, "110 dmg, school 32, 30s, every 3s -> 10 ticks of 11.0"),
    # --- finishers (Coup de grâce): per-combo table, clamped to the points spent ---
    ("Déchirure", "Coup de grâce qui inflige des dégâts sur la durée. Les dégâts augmentent avec le nombre de points de combo et votre puissance d'attaque : 1 point : 44 points de dégâts en 12 sec. 2 points : 71 points de dégâts en 12 sec. 3 points : 97 points de dégâts en 12 sec. 4 points : 124 points de dégâts en 12 sec. 5 points : 150 points de dégâts en 12 sec.",
     5, "150 dmg, school 1, 12s, every 2s -> 6 ticks of 25.0"),
    ("Déchirure", "Coup de grâce qui inflige des dégâts sur la durée. Les dégâts augmentent avec le nombre de points de combo et votre puissance d'attaque : 1 point : 44 points de dégâts en 12 sec. 2 points : 71 points de dégâts en 12 sec. 3 points : 97 points de dégâts en 12 sec. 4 points : 124 points de dégâts en 12 sec. 5 points : 150 points de dégâts en 12 sec.",
     1, "44 dmg, school 1, 12s, every 2s -> 6 ticks of 7.3"),
    ("Rupture", "Coup de grâce qui inflige des dégâts sur la durée. Les dégâts augmentent avec votre puissance d'attaque et l'effet dure plus longtemps selon le nombre de points de combo : 1 point : 25 points de dégâts en 8 s 2 points : 37 points de dégâts en 10 s 3 points : 51 points de dégâts en 12 s 4 points : 68 points de dégâts en 14 s 5 points : 87 points de dégâts en 16 s",
     5, "87 dmg, school 1, 16s, every 2s -> 8 ticks of 10.9"),
    # --- heal over time: never a DoT ---
    ("Rénovation", "Rend 45 points de vie à la cible en 15 sec.", None, "not tracked"),
    # --- direct-damage poison proc: no "en N sec", so not a DoT ---
    ("Poison instantané", "13 à 17 points de dégâts de nature.", None, "not tracked"),
    # --- ignored by name: several of these WOULD parse as a DoT if the French name weren't mapped ---
    ("Pluie de feu", "Invoque une pluie de feu qui brûle les adversaires dans la zone d'effet.",
     None, "ignored (list)"),
    ("Flammes infernales", "Enflamme la zone qui entoure le lanceur de sorts.", None, "ignored (list)"),
    ("Choc de flammes", "Invoque un pilier de feu qui inflige 55 à 71 points de dégâts de feu et 44 points de dégâts de feu supplémentaires en 8 sec.",
     None, "ignored (list)"),
    ("Salve", "Tire une salve sur la zone ciblée. Inflige 70 points de dégâts des arcanes toutes les 1 s pendant 6 sec.",
     None, "ignored (list)"),
    ("Ouragan", "Crée une violente tempête qui inflige 69 points de dégâts de nature toutes les 1 s. Dure 10 sec.",
     None, "ignored (list)"),
    ("Consécration", "Consacre le sol et inflige 16 points de dégâts du sacré en 8 sec aux adversaires qui entrent dans la zone.",
     None, "ignored (list)"),
    ("Projectiles des arcanes", "Lance des projectiles des arcanes sur l'ennemi et inflige 25 points de dégâts des Arcanes toutes les secondes pendant 3 sec.",
     None, "ignored (list)"),
    ("Éclats stellaires", "Une pluie d'éclats lunaires s'abat sur la tête de l'ennemi et lui inflige 162 points de dégâts des Arcanes en 6 sec.",
     None, "ignored (list)"),
    ("Drain de vie", "Transfère 10 points de vie de la cible vers le personnage lanceur toutes les 1 s. Dure 5 sec.",
     None, "ignored (list)"),
    ("Siphon d'âme", "Draine l'âme de la cible et lui inflige 85 points de dégâts d'ombre en 15 sec.",
     None, "ignored (list)"),
    ("Fouet mental", "Attaque l'esprit de la cible avec l'énergie de l'ombre, ce qui lui inflige 63 points de dégâts d'ombre en 3 sec et réduit sa vitesse de déplacement de 50 %.",
     None, "ignored (list)"),
    ("Drain de mana", "Transfère 44 points de mana toutes les 1 s de la cible vers le personnage lanceur. Dure 5 sec.",
     None, "ignored (list)"),
    ("Captation de vie", "Rend 12 points de vie toutes les secondes au familier du personnage lanceur pendant 10 sec.",
     None, "ignored (list)"),
]

# A few things the tables alone don't cover: combo-point award detection and the finisher predicate.
EXTRA = [
    ("comboAwarded(Garrot)", ns.parser.comboAwarded("... Vous gagnez 1 point de combo."), 1),
    ("comboAwarded(no combo line)", ns.parser.comboAwarded("Inflige 40 points de dégâts d'Ombre en 12 sec."), None),
    ("isFinisher(Déchirure)", ns.parser.isFinisher("Coup de grâce qui inflige des dégâts sur la durée."), True),
    ("isFinisher(Corruption)", ns.parser.isFinisher("Corrompt la cible et lui inflige 40 points de dégâts."), False),
    ("canon(Plaie d'agonie)", ns.canonicalName("Plaie d'agonie"), "Bane of Agony"),
    ("canon(Siphon d'âme)", ns.canonicalName("Siphon d'âme"), "Drain Soul"),
    ("canon(unknown FR spell)", ns.canonicalName("Sort inconnu"), "Sort inconnu"),
]

if __name__ == "__main__":
    width = max(len(c[0]) for c in CASES)
    failures = 0
    for name, desc, cp, expect in CASES:
        got = track(name, desc, cp)
        ok = got == expect
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:<{width}}  {got}" + ("" if ok else f"   (expected {expect})"))
    print()
    for label, got, expect in EXTRA:
        got = None if got is None else (got if isinstance(got, (bool,)) else got)
        ok = got == expect
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:<34} {got}" + ("" if ok else f"   (expected {expect})"))
    print()
    print("all passed" if not failures else f"{failures} FAILED")
    sys.exit(1 if failures else 0)
