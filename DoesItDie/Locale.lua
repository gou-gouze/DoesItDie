-- DoesItDie — localization
--
-- The addon reads your spell casts: the spell NAME (C_Spell.GetSpellName) and its DESCRIPTION
-- (C_Spell.GetSpellDescription). Both are translated on a non-English client, so the English parser in
-- DoesItDie.lua (which matches phrases like "damage over N sec" and keys its tables by English spell name)
-- doesn't work there. This file supplies, per GetLocale():
--
--   * ns.parser       — a replacement description parser for the client's language (nil on enUS, so
--                       DoesItDie.lua keeps its own English parser). Interface:
--                         parse(desc, comboPoints) -> total, school, duration[, statedInterval]  (like parseDot)
--                         isFinisher(desc)         -> boolean   (desc is a plain, non-secret string)
--                         comboAwarded(desc)       -> number or nil
--   * ns.canonicalName(name) — maps the client's spell name back to the English name DoesItDie.lua keys its
--                       IGNORED_SPELLS / KNOWN_TICK_INTERVALS / SCHOOL_BY_NAME / TICK_SHAPES / PROJECTILE_DOTS
--                       tables by. Identity on enUS and on any locale without a map.
--
-- The displayed DoT name stays the client's own (French) name; only table lookups and parsing are localized.
--
-- French data was taken from WoW: Forever's own French tooltips (Wowhead, data env Forever, locale fr) for
-- every spell the tables reference; a few names not reachable there fall back to the standard Classic French
-- name and are marked "standard FR, confirm in-game". Nothing here is verified on a French client yet.

local _, ns = ...

ns.locale = (type(GetLocale) == "function" and GetLocale()) or "enUS"

-- Default: identity. A locale below may replace it.
ns.canonicalName = function(name) return name end

---------------------------------------------------------------------------
-- frFR
---------------------------------------------------------------------------

if ns.locale == "frFR" then
    -- School masks (same values DoesItDie.lua uses). Frostfire reports as Frost+Fire OR'd.
    local PHYSICAL = 1

    -- Lowercase a string and drop French accents, so name/text matching is immune to accent and case
    -- differences between data sources and the live client ("Éclat"/"Eclat", "d'Ombre"/"d'ombre",
    -- straight ' vs curly ’). Operates on UTF-8 bytes (WoW frFR text is UTF-8).
    local ACCENTS = {
        ["\195\137"] = "e", ["\195\169"] = "e", ["\195\136"] = "e", ["\195\168"] = "e", -- É é È è
        ["\195\138"] = "e", ["\195\170"] = "e", ["\195\139"] = "e", ["\195\171"] = "e", -- Ê ê Ë ë
        ["\195\128"] = "a", ["\195\160"] = "a", ["\195\130"] = "a", ["\195\162"] = "a", -- À à Â â
        ["\195\142"] = "i", ["\195\174"] = "i", ["\195\143"] = "i", ["\195\175"] = "i", -- Î î Ï ï
        ["\195\148"] = "o", ["\195\180"] = "o",                                         -- Ô ô
        ["\195\155"] = "u", ["\195\187"] = "u", ["\195\153"] = "u", ["\195\185"] = "u", -- Û û Ù ù
        ["\195\135"] = "c", ["\195\167"] = "c",                                         -- Ç ç
        ["\226\128\153"] = "'",                                                         -- ’ -> '
    }
    local function strip(s)
        s = s:gsub("\226\128\153", "'")
        s = s:gsub("\195[\128-\191]", ACCENTS)
        return (s:lower():gsub("^%s+", ""):gsub("%s+$", ""))
    end

    -- English name (the key DoesItDie.lua uses) = French name on Forever. Only spells referenced by one of the
    -- lookup tables strictly need an entry; the rest are included for completeness and documentation.
    -- "F:" = confirmed from Forever's French tooltip; "S:" = standard Classic French name, confirm in-game.
    local FR_NAME = {
        -- tracked DoTs (display only; no table lookup needs these, kept for reference)
        ["Corruption"]          = "Corruption",             -- F
        ["Moonfire"]            = "Éclat lunaire",          -- F
        ["Devouring Plague"]    = "Peste dévorante",        -- F
        ["Shadow Word: Pain"]   = "Mot de l'ombre : Douleur", -- F
        ["Garrote"]             = "Garrot",                 -- F
        ["Rake"]                = "Griffure",               -- F
        ["Rend"]                = "Pourfendre",             -- F
        ["Entangling Roots"]    = "Sarments",               -- F
        ["Immolate"]            = "Immolation",             -- S
        ["Flame Shock"]         = "Choc de feu",            -- S
        -- KNOWN_TICK_INTERVALS / TICK_SHAPES
        ["Insect Swarm"]        = "Nuée d'insectes",        -- S
        -- Forever renamed Curse of Agony to Bane of Agony (both English keys exist in the tables with the same
        -- values); map the one French name to Bane of Agony so canonicalName is deterministic.
        ["Bane of Agony"]       = "Plaie d'agonie",         -- F (spell 980)
        ["Fireball"]            = "Boule de feu",           -- F
        ["Holy Fire"]           = "Flammes sacrées",        -- F
        ["Rip"]                 = "Déchirure",              -- F
        ["Rupture"]             = "Rupture",                -- F
        -- SCHOOL_BY_NAME
        ["Siphon Life"]         = "Siphon de vie",          -- F
        -- PROJECTILE_DOTS
        ["Serpent Sting"]       = "Morsure de serpent",     -- F
        ["Pyroblast"]           = "Explosion pyrotechnique", -- F
        ["Frostfire Bolt"]      = "Trait de givrefeu",      -- S (Forever custom; confirm name in-game)
        -- IGNORED_SPELLS
        ["Rain of Fire"]        = "Pluie de feu",           -- F
        ["Hellfire"]            = "Flammes infernales",     -- F
        ["Blizzard"]            = "Blizzard",               -- S
        ["Flamestrike"]         = "Choc de flammes",        -- F
        ["Consecration"]        = "Consécration",           -- F
        ["Hurricane"]           = "Ouragan",                -- F
        ["Volley"]              = "Salve",                  -- F
        ["Drain Life"]          = "Drain de vie",           -- F
        ["Drain Soul"]          = "Siphon d'âme",           -- F
        ["Drain Mana"]          = "Drain de mana",          -- F
        ["Health Funnel"]       = "Captation de vie",       -- F
        ["Mind Flay"]           = "Fouet mental",           -- F
        ["Arcane Missiles"]     = "Projectiles des arcanes", -- F
        ["Starshards"]          = "Éclats stellaires",      -- F
        ["Immolation Trap"]     = "Piège immolation",       -- S
        ["Explosive Trap"]      = "Piège explosif",         -- S
        ["Wyvern Sting"]        = "Piqûre de wyverne",      -- S
    }
    -- Invert into normalized French name -> English key.
    local EN_BY_FR = {}
    for en, fr in pairs(FR_NAME) do EN_BY_FR[strip(fr)] = en end

    ns.canonicalName = function(name)
        if type(name) ~= "string" then return name end
        return EN_BY_FR[strip(name)] or name
    end

    -- School of a damage clause, read from the fragment between "points de dégâts" and "en N sec". French
    -- states the school after the number ("... points de dégâts d'Ombre en 12 sec"), with inconsistent case
    -- and connector ("d'Ombre", "de Feu", "des Arcanes", "du Sacré"), so match accent-free lowercase stems.
    local SCHOOL_STEMS = {
        { "givrefeu", 4 + 16 }, -- combined; wins over its "givre"/"feu" parts
        { "ombre",    32 },
        { "arcane",   64 },     -- Arcanes
        { "givre",    16 },
        { "feu",       4 },
        { "nature",    8 },
        { "sacr",      2 },     -- Sacré
        { "physique",  1 },
    }
    local function schoolOf(fragment)
        local f = strip(fragment)
        for _, pair in ipairs(SCHOOL_STEMS) do
            if f:find(pair[1], 1, true) then return pair[2] end
        end
        return PHYSICAL
    end

    -- Finishers list a DoT per combo point, e.g.:
    --   " 1 point : 44 points de dégâts en 12 sec."   (Déchirure/Rip)
    --   " 1 point : 25 points de dégâts en 8 s"        (Rupture; "s" not "sec")
    local function parseFinisher(desc, comboPoints)
        local byPoints, highest = {}, 0
        for pts, amount, secs in desc:gmatch("(%d+)%s*points?%s*:%s*(%d+)%s*points de dégâts en%s+(%d+%.?%d*)") do
            local points = tonumber(pts)
            byPoints[points] = { total = tonumber(amount), duration = tonumber(secs) }
            highest = math.max(highest, points)
        end
        if highest == 0 then return nil end
        local entry = byPoints[math.max(1, math.min(comboPoints, highest))] or byPoints[highest]
        return entry.total, PHYSICAL, entry.duration
    end

    local function isFinisher(desc)
        return desc:find("Coup de grâce") ~= nil
    end

    local parser = {}

    function parser.isFinisher(desc)
        return isFinisher(desc)
    end

    function parser.comboAwarded(desc)
        -- Builders read "Vous gagnez N point(s) de combo."
        return tonumber(desc:match("[Vv]ous gagnez%s+(%d+)%s*points? de combo"))
    end

    function parser.parse(desc, comboPoints)
        if isFinisher(desc) then return parseFinisher(desc, comboPoints or 5) end
        -- Weapon enchants (rogue poisons) read "Enduit une arme...": a proc DoT, not cast on the target.
        if desc:find("[Ee]nduit") then return nil end
        -- Heals over time ("Rend/Soigne/Restaure N points de vie ... "): never a damage DoT.
        if desc:find("^Rend ") or desc:find("^Soigne") or desc:find("^Restaure") then return nil end

        -- Periodic damage: take the LAST "<n> points de dégâts <school...> en <secs> sec" clause, so a spell
        -- with a direct hit first (Immolation, Éclat lunaire, Boule de feu) yields its periodic part. The
        -- middle class excludes digits/dots so it can't jump across to another clause's number.
        local total, school, duration
        for amount, mid, secs in desc:gmatch("(%d+)%s*points de dégâts([^%d.]*)en%s+(%d+%.?%d*)%s*s") do
            total, school, duration = tonumber(amount), schoolOf(mid), tonumber(secs)
        end
        if total and duration and duration > 0 then return total, school, duration end

        -- Physical bleed stated as health loss: "... saigne et perd <n> points de vie en <secs> sec" (Pourfendre).
        local amount, secs = desc:match("perd%s+(%d+)%s*points de vie en%s+(%d+%.?%d*)%s*s")
        if amount and secs then return tonumber(amount), PHYSICAL, tonumber(secs) end

        -- Health drain stated as a rate: "Transfère <n> points de vie ... toutes les <every> s. Dure <lasts> sec"
        -- (Siphon de vie). Its school comes from SCHOOL_BY_NAME in the caller. Drain de vie/Drain de mana read the
        -- same way but are ignored by name before reaching here.
        local hp, every = desc:match("Transfère%s+(%d+)%s*points de vie.-toutes les%s+(%d+%.?%d*)%s*s")
        local lasts = desc:match("[Dd]ure%s+(%d+%.?%d*)%s*s")
        if hp and every and lasts then
            every, lasts = tonumber(every), tonumber(lasts)
            if every > 0 and lasts > 0 then
                return tonumber(hp) * math.floor(lasts / every + 0.5), PHYSICAL, lasts, every
            end
        end
    end

    ns.parser = parser
end
