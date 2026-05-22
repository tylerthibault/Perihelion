from spacesim import (
    GALAXIES,
    GALAXY_SYSTEM_MAX,
    GALAXY_TARGET,
    PLANETS,
    SECTOR_PLANET_MAX_PER_SYSTEM,
    SECTOR_SYSTEM_TARGET,
    STARTING_KNOWN_SYSTEM_IDS,
    STATIONS,
    SYSTEMS,
    SYSTEM_STATIONS,
    GALAXY_SYSTEM_ID_BY_INDEX,
    SYSTEM_GALAXY_INDEX,
    SYSTEM_ID_BY_INDEX,
    SYSTEM_INDEX,
    CORE_SYSTEM_IDS,
    apply_action,
    ascent_segment,
    branch_system_ids,
    cargo_used,
    create_game,
    descent_segment,
    fuel_cost,
    generate_planet_place,
    local_route_preview,
    market_prices,
    planet_flight_stats,
    public_state,
    _generated_system_name,
    _slug,
)


def stock_upgrade_materials(game, amount=20):
    for good in game["inventory"]:
        game["inventory"][good] = amount


def stock_materials_for_upgrade(game, upgrade_id):
    offer = next(upgrade for upgrade in public_state(game)["ship"]["upgrades"] if upgrade["id"] == upgrade_id)
    for material in offer["materials"]:
        game["inventory"][material["id"]] = material["required"]
    return offer


def test_buying_cargo_spends_credits_and_uses_space():
    game = create_game()

    updated, message = apply_action(game, "buy", {"good": "water", "quantity": 3})

    assert "Bought 3 Water" in message
    assert updated["credits"] == game["credits"] - 27
    assert updated["inventory"]["water"] == 3
    assert cargo_used(updated) == 3


def test_travel_consumes_fuel_and_changes_location():
    game = create_game()
    destination = "kepler"
    cost = fuel_cost(game["location"], destination)

    game, _ = apply_action(game, "explore", {})
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})
    updated, message = apply_action(game, "travel", {"destination": destination})

    assert "Arrived at Kepler Reach" in message
    assert updated["location"] == destination
    assert updated["fuel"] == game["fuel"] - cost
    assert updated["day"] > game["day"]
    assert updated["travel_state"] == "system_space"


def test_accepting_a_mission_adds_active_contract():
    game = create_game()
    game["known_systems"] = ["aurora", "kepler"]
    game["charted_systems"] = ["aurora", "kepler"]
    mission_id = public_state(game)["missions"][0]["id"]

    updated, message = apply_action(game, "accept_mission", {"missionId": mission_id})

    assert "Accepted contract" in message
    assert updated["active_mission"]["id"] == mission_id


def test_cannot_buy_past_available_cargo_space():
    game = create_game()

    updated, message = apply_action(game, "buy", {"good": "ore", "quantity": 15})

    assert "hold cannot fit" in message
    assert updated["inventory"]["ore"] == 0


def test_state_includes_station_areas_and_condition_based_planet_places():
    state = public_state(create_game())

    assert state["station"]["areas"]
    assert state["stations"]
    assert state["planets"]
    assert state["planets"][0]["placeCount"] > 0
    assert state["planets"][0]["places"]


def test_sector_has_ten_thousand_virtual_systems_with_lazy_generation():
    assert SECTOR_SYSTEM_TARGET <= GALAXY_SYSTEM_MAX
    assert GALAXY_SYSTEM_MAX == 5_000
    assert SECTOR_PLANET_MAX_PER_SYSTEM == 10
    assert GALAXY_TARGET * GALAXY_SYSTEM_MAX * SECTOR_PLANET_MAX_PER_SYSTEM >= 1_000_000
    assert len(SYSTEMS) < SECTOR_SYSTEM_TARGET
    assert all(1 <= len(planets) <= SECTOR_PLANET_MAX_PER_SYSTEM for planets in PLANETS.values())
    assert all(galaxy["size"] <= GALAXY_SYSTEM_MAX for galaxy in GALAXIES.values())
    assert all(system["galaxyId"] for system in SYSTEMS.values())
    assert any(len(stations) > 1 for stations in SYSTEM_STATIONS.values())


def test_small_planets_have_zero_to_twenty_locations():
    small_counts = [
        planet["placeCount"]
        for planets in PLANETS.values()
        for planet in planets
        if planet.get("sizeClass") == "small" or any(word in planet["type"] for word in ("moon", "dwarf", "fractured"))
    ]

    assert small_counts
    assert max(small_counts) <= 20
    assert any(count == 0 for count in small_counts)


def test_state_includes_galaxy_catalog_system_details():
    game = create_game()
    game["known_systems"] = ["aurora", "morrow"]
    game["charted_systems"] = ["aurora", "morrow"]
    state = public_state(game)
    morrow = next(system for system in state["systemCatalog"] if system["id"] == "morrow")

    assert morrow["resources"]
    assert morrow["station"]["areaCount"] == len(morrow["station"]["areas"])
    assert morrow["planets"]
    assert morrow["planets"][0]["flightStats"]["gravity"] > 0
    assert morrow["planets"][0]["resourceHints"]


def test_exploring_reveals_uncharted_branch_signals():
    game = create_game()
    game["location"] = STARTING_KNOWN_SYSTEM_IDS[-1]
    game["travel_state"] = "docked"

    initial = public_state(game)
    updated, message = apply_action(game, "explore", {})
    state = public_state(updated)
    signals = [system for system in state["systemCatalog"] if not system["charted"]]

    assert initial["discovery"]["known"] == len(STARTING_KNOWN_SYSTEM_IDS)
    assert initial["discovery"]["charted"] == len(STARTING_KNOWN_SYSTEM_IDS)
    assert initial["discovery"]["uncharted"] == 0
    assert initial["discovery"]["total"] == SECTOR_SYSTEM_TARGET
    assert initial["discovery"]["potentialPlanets"] == SECTOR_SYSTEM_TARGET * SECTOR_PLANET_MAX_PER_SYSTEM
    assert initial["discovery"]["currentBranches"] == 3
    assert "revealed 3 uncharted signals" in message
    assert state["discovery"]["known"] == len(STARTING_KNOWN_SYSTEM_IDS) + 3
    assert state["discovery"]["charted"] == len(STARTING_KNOWN_SYSTEM_IDS)
    assert len(signals) == 3
    assert signals[0]["resources"] == []
    assert signals[0]["planets"] == []


def test_arriving_at_uncharted_signal_charts_the_real_system():
    game = create_game()
    game["location"] = STARTING_KNOWN_SYSTEM_IDS[-1]
    game["travel_state"] = "system_space"
    game["near_body"] = {"type": "system", "id": game["location"], "name": SYSTEMS[game["location"]]["name"], "placeId": None}
    game, _ = apply_action(game, "explore", {})
    destination = next(system_id for system_id in game["known_systems"] if system_id not in game["charted_systems"])
    game["ship_upgrades"]["fuel_tanks"] = 3
    game["fuel"] = 36

    updated, message = apply_action(game, "travel", {"destination": destination})
    state = public_state(updated)
    charted_system = next(system for system in state["systemCatalog"] if system["id"] == destination)

    assert "resolved into a charted system" in message
    assert destination in updated["charted_systems"]
    assert charted_system["charted"] is True
    assert charted_system["planets"]


def test_second_tier_scan_generates_systems_on_demand():
    game = create_game()
    game["location"] = STARTING_KNOWN_SYSTEM_IDS[-2]
    generated_before = len(SYSTEMS)

    updated, message = apply_action(game, "explore", {})
    state = public_state(updated)

    assert "revealed 3 uncharted signals" in message
    assert len(SYSTEMS) > generated_before
    assert state["discovery"]["known"] == len(STARTING_KNOWN_SYSTEM_IDS) + 3
    assert state["discovery"]["charted"] == len(STARTING_KNOWN_SYSTEM_IDS)


def test_generated_current_location_recovers_after_cache_miss():
    generated_index = 420
    system_index = len(CORE_SYSTEM_IDS) + generated_index - 1
    system_id = _slug(_generated_system_name(generated_index))
    SYSTEMS.pop(system_id, None)
    STATIONS.pop(system_id, None)
    SYSTEM_STATIONS.pop(system_id, None)
    PLANETS.pop(system_id, None)
    SYSTEM_INDEX.pop(system_id, None)
    SYSTEM_GALAXY_INDEX.pop(system_id, None)
    SYSTEM_ID_BY_INDEX.pop(system_index, None)
    GALAXY_SYSTEM_ID_BY_INDEX.pop(("aurora-thread", system_index), None)

    game = create_game()
    game["location"] = system_id
    game["known_systems"] = [system_id]
    game["charted_systems"] = [system_id]
    game.pop("current_place", None)

    state = public_state(game)

    assert state["location"] == system_id
    assert state["currentSystem"]["name"] == _generated_system_name(generated_index)
    assert system_id in STATIONS


def test_state_includes_current_galaxy_and_fold_gates():
    state = public_state(create_game())
    gate = next(gate for gate in state["gates"] if gate["type"] == "system")

    assert state["currentGalaxy"]["name"] == "Aurora Thread"
    assert state["currentGalaxy"]["size"] == SECTOR_SYSTEM_TARGET
    assert state["knownGalaxies"][0]["id"] == state["currentGalaxy"]["id"]
    assert {system["id"] for system in state["systems"]} == set(STARTING_KNOWN_SYSTEM_IDS)
    assert len([gate for gate in state["gates"] if gate["type"] == "system"]) >= 3
    assert gate["hidden"] is False
    assert gate["destinationGalaxyId"] != state["currentGalaxy"]["id"]
    assert gate["fee"] > 0


def test_existing_starter_save_migrates_to_expanded_galaxy():
    game = create_game()
    game["known_systems"] = ["aurora", "kepler", "vesta", "eirene", "morrow", "solace"]
    game["charted_systems"] = game["known_systems"][:]

    state = public_state(game)

    assert {system["id"] for system in state["systems"]} == set(STARTING_KNOWN_SYSTEM_IDS)
    assert state["discovery"]["charted"] == len(STARTING_KNOWN_SYSTEM_IDS)


def test_normal_jump_to_another_galaxy_is_blocked():
    game = create_game()
    gate = next(gate for gate in public_state(game)["gates"] if gate["type"] == "system")
    destination = gate["destinationSystemId"]
    game["known_systems"].append(destination)
    game["charted_systems"].append(destination)
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})

    updated, message = apply_action(game, "travel", {"destination": destination})

    assert "Intergalactic jump blocked" in message
    assert updated["location"] == "aurora"


def test_gate_use_requires_system_space():
    game = create_game()
    gate = next(gate for gate in public_state(game)["gates"] if gate["type"] == "system")

    updated, message = apply_action(game, "use_gate", {"gateId": gate["id"]})

    assert "requires system space" in message
    assert updated["location"] == "aurora"


def test_system_built_gate_transit_charges_fee_and_uses_no_fuel():
    game = create_game()
    gate = next(gate for gate in public_state(game)["gates"] if gate["type"] == "system")
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})
    fuel_before = game["fuel"]
    credits_before = game["credits"]

    updated, message = apply_action(game, "use_gate", {"gateId": gate["id"]})
    state = public_state(updated)

    assert "Coordinate fold complete" in message
    assert updated["location"] == gate["destinationSystemId"]
    assert updated["fuel"] == fuel_before
    assert updated["credits"] == credits_before - gate["fee"]
    assert state["currentGalaxy"]["id"] == gate["destinationGalaxyId"]
    assert gate["destinationSystemId"] in updated["charted_systems"]


def test_ancient_gate_hides_destination_until_used():
    game = create_game()
    game["location"] = "morrow"
    game["current_place"] = "station:morrow:clamps"
    game["known_systems"] = ["aurora", "morrow"]
    game["charted_systems"] = ["aurora", "morrow"]
    state = public_state(game)

    ancient_gate = next(gate for gate in state["gates"] if gate["type"] == "ancient")

    assert ancient_gate["hidden"] is True
    assert ancient_gate["destinationSystemId"] == ""
    assert ancient_gate["destinationGalaxyName"] == "Hidden fold shadow"


def test_ancient_gate_reveals_destination_after_transit():
    game = create_game()
    game["location"] = "morrow"
    game["current_place"] = "station:morrow:clamps"
    game["travel_state"] = "system_space"
    game["near_body"] = {"type": "system", "id": "morrow", "name": "Morrow Rift", "placeId": None}
    game["known_systems"] = ["aurora", "morrow"]
    game["charted_systems"] = ["aurora", "morrow"]
    ancient_gate = next(gate for gate in public_state(game)["gates"] if gate["type"] == "ancient")

    updated, message = apply_action(game, "use_gate", {"gateId": ancient_gate["id"]})
    state = public_state(updated)

    assert "Ancient telemetry resolved" in message
    assert updated["location"] != "morrow"
    assert ancient_gate["id"] in updated["used_gates"]
    assert len(state["knownGalaxies"]) == 2


def test_unlimited_credits_bypasses_gate_fee():
    game = create_game()
    game["credits"] = 0
    game, _ = apply_action(game, "set_cheat", {"cheat": "unlimitedCredits", "enabled": True})
    gate = next(gate for gate in public_state(game)["gates"] if gate["type"] == "system")
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})

    updated, message = apply_action(game, "use_gate", {"gateId": gate["id"]})

    assert "unlimited credits covered" in message
    assert updated["credits"] == 0
    assert updated["location"] == gate["destinationSystemId"]


def test_player_built_anchors_link_owned_systems_without_fuel():
    game = create_game()
    game["credits"] = 3000
    stock_upgrade_materials(game)
    game, message = apply_action(game, "build_gate_anchor", {})

    assert "fold anchor deployed" in message
    assert game["player_gate_anchors"] == ["aurora"]

    game, _ = apply_action(game, "explore", {})
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})
    game, _ = apply_action(game, "travel", {"destination": "kepler"})
    game, _ = apply_action(game, "local_travel", {"movement": "dock_station"})
    game["credits"] = 3000
    stock_upgrade_materials(game)
    game, _ = apply_action(game, "build_gate_anchor", {})
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})
    player_gate = next(gate for gate in public_state(game)["gates"] if gate["type"] == "player")
    fuel_before = game["fuel"]

    updated, message = apply_action(game, "use_gate", {"gateId": player_gate["id"]})

    assert "Coordinate fold complete" in message
    assert updated["location"] == "aurora"
    assert updated["fuel"] == fuel_before


def test_cannot_travel_to_undiscovered_system():
    game = create_game()
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})
    destination = branch_system_ids(STARTING_KNOWN_SYSTEM_IDS[-1])[0]

    updated, message = apply_action(game, "travel", {"destination": destination})

    assert "not been discovered" in message
    assert updated["location"] == "aurora"


def test_planet_place_generation_is_deterministic():
    planet = PLANETS["aurora"][0]

    first = generate_planet_place(planet, 1274)
    second = generate_planet_place(planet, 1274)

    assert first == second
    assert first["id"] == "planet:new-lumen:1274"


def test_visiting_planet_place_is_persistent():
    game = create_game()
    place_id = public_state(game)["planets"][0]["places"][0]["id"]

    updated, message = apply_action(game, "visit_place", {"placeId": place_id})

    assert "Expedition reached" in message
    assert updated["current_place"] == place_id
    assert updated["visited_places"][place_id] == 1
    assert updated["day"] > game["day"]
    assert updated["fuel"] < game["fuel"]
    assert updated["travel_state"] == "landed"
    assert public_state(updated)["currentPlace"]["visited"] is True


def test_scanning_planet_rotates_visible_place_samples():
    game = create_game()
    state = public_state(game)
    planet_id = state["planets"][0]["id"]
    first_ids = [place["id"] for place in state["planets"][0]["places"]]

    updated, message = apply_action(game, "scan_planet", {"planetId": planet_id})
    second_ids = [place["id"] for place in public_state(updated)["planets"][0]["places"]]

    assert "Survey filters" in message
    assert first_ids != second_ids


def test_resource_source_systems_have_cheaper_local_goods():
    aurora = create_game()
    vesta = create_game()
    vesta["location"] = "vesta"
    vesta["current_place"] = "station:vesta:forge"
    solace = create_game()
    solace["location"] = "solace"
    solace["current_place"] = "station:solace:triage"

    assert market_prices(vesta)["ore"] < market_prices(aurora)["ore"]
    assert market_prices(solace)["medicine"] < market_prices(vesta)["medicine"]


def test_trade_market_includes_basic_upgrade_materials():
    state = public_state(create_game())
    market_goods = {item["id"] for item in state["market"]}
    inventory_goods = {item["id"] for item in state["inventory"]}
    upgrade_materials = {
        material["id"]
        for upgrade in state["ship"]["upgrades"]
        for material in upgrade["materials"]
    }
    expected = {"alloys", "polymers", "ceramics", "composites", "coolant", "electronics"}

    assert expected <= market_goods
    assert expected <= inventory_goods
    assert expected & upgrade_materials


def test_local_place_changes_market_prices_inside_same_system():
    game = create_game()
    station_ore = market_prices(game)["ore"]

    updated, _ = apply_action(game, "visit_place", {"placeId": "planet:new-lumen:1"})

    assert market_prices(updated)["ore"] < station_ore
    assert public_state(updated)["marketContext"]["name"] == "Iron Depot 0001"


def test_cannot_jump_until_ship_reaches_system_space():
    game = create_game()
    game, _ = apply_action(game, "explore", {})

    blocked, message = apply_action(game, "travel", {"destination": "kepler"})

    assert "Jump blocked" in message
    assert blocked["location"] == "aurora"

    undocked, message = apply_action(game, "local_travel", {"movement": "undock"})

    assert "Undock complete" in message
    assert public_state(undocked)["travelState"]["canJump"] is True


def test_cannot_jump_while_landed():
    game = create_game()
    game, _ = apply_action(game, "explore", {})
    place_id = public_state(game)["planets"][0]["places"][0]["id"]
    landed, _ = apply_action(game, "local_travel", {"movement": "land", "placeId": place_id})

    updated, message = apply_action(landed, "travel", {"destination": "kepler"})

    assert "Jump blocked" in message
    assert updated["location"] == "aurora"
    assert updated["travel_state"] == "landed"


def test_planet_flight_stats_are_deterministic():
    planet = PLANETS["kepler"][0]

    first = planet_flight_stats(planet)
    second = planet_flight_stats(planet)

    assert first == second
    assert first["gravity"] > 0
    assert first["atmosphereDensity"] > 0


def test_gravity_and_atmosphere_affect_launch_and_landing_costs():
    moon = PLANETS["aurora"][1]
    storm_world = PLANETS["kepler"][0]

    assert ascent_segment(storm_world)["fuelCost"] > ascent_segment(moon)["fuelCost"]
    assert descent_segment(storm_world)["fuelCost"] > descent_segment(moon)["fuelCost"]


def test_rescue_refuel_works_away_from_station():
    game = create_game()
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})
    game["fuel"] = 0

    updated, message = apply_action(game, "rescue_refuel", {})

    assert "Rescue Tanker delivered" in message
    assert updated["fuel"] > 0
    assert updated["day"] > game["day"]


def test_fuel_tank_upgrade_increases_capacity_and_refuel_target():
    game = create_game()
    game["credits"] = 1000
    offer = stock_materials_for_upgrade(game, "fuel_tanks")

    upgraded, message = apply_action(game, "buy_upgrade", {"upgradeId": "fuel_tanks"})
    state = public_state(upgraded)

    assert "Auxiliary Fuel Tanks tier 1" in message
    assert upgraded["credits"] == game["credits"] - offer["nextCost"]
    assert state["maxFuel"] == 24
    assert state["fuel"] == 18
    for material in offer["materials"]:
        assert upgraded["inventory"][material["id"]] == game["inventory"][material["id"]] - material["required"]

    refueled, message = apply_action(upgraded, "refuel", {})

    assert "Loaded 6 fuel" in message
    assert refueled["fuel"] == 24


def test_cargo_bay_upgrade_expands_trade_capacity():
    game = create_game()
    game["credits"] = 2000
    stock_materials_for_upgrade(game, "cargo_bays")

    upgraded, _ = apply_action(game, "buy_upgrade", {"upgradeId": "cargo_bays"})
    updated, message = apply_action(upgraded, "buy", {"good": "ore", "quantity": 18})

    assert public_state(upgraded)["cargoCapacity"] == 36
    assert "Bought 18 Ore" in message
    assert cargo_used(updated) == 36


def test_ship_upgrades_require_docking():
    game = create_game()
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})

    updated, message = apply_action(game, "buy_upgrade", {"upgradeId": "fuel_tanks"})

    assert "Dock at the station" in message
    assert updated["ship_upgrades"] == {}


def test_jump_drive_upgrade_reduces_plotted_fuel_cost():
    game = create_game()
    game["location"] = "kepler"
    game["current_place"] = "station:kepler:gantry"
    game["known_systems"] = ["aurora", "kepler", "eirene"]
    game["charted_systems"] = ["aurora", "kepler", "eirene"]
    game["credits"] = 2000
    stock_upgrade_materials(game)
    game, _ = apply_action(game, "buy_upgrade", {"upgradeId": "jump_drive"})
    game, _ = apply_action(game, "buy_upgrade", {"upgradeId": "jump_drive"})
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})

    route = next(route for route in public_state(game)["travel"] if route["id"] == "eirene")

    assert route["fuelCost"] < fuel_cost("kepler", "eirene")
    assert route["fuelCost"] == 9


def test_maneuvering_thrusters_reduce_local_fuel_costs():
    game = create_game()
    place_id = public_state(game)["planets"][0]["places"][0]["id"]
    base_preview = local_route_preview(game, "land", place_id=place_id)
    game["credits"] = 1000
    stock_upgrade_materials(game)

    upgraded, _ = apply_action(game, "buy_upgrade", {"upgradeId": "maneuver_thrusters"})
    upgraded, _ = apply_action(upgraded, "buy_upgrade", {"upgradeId": "maneuver_thrusters"})
    upgraded_preview = local_route_preview(upgraded, "land", place_id=place_id)

    assert upgraded_preview["fuelCost"] < base_preview["fuelCost"]
    assert upgraded_preview["baseFuelCost"] == base_preview["fuelCost"]


def test_upgrade_offers_depend_on_current_location():
    aurora = public_state(create_game())
    kepler = create_game()
    kepler["location"] = "kepler"
    kepler["current_place"] = "station:kepler:gantry"
    kepler["known_systems"] = ["aurora", "kepler"]
    kepler["charted_systems"] = ["aurora", "kepler"]
    kepler_state = public_state(kepler)

    aurora_offers = {upgrade["id"] for upgrade in aurora["ship"]["upgrades"] if upgrade["availableHere"]}
    kepler_offers = {upgrade["id"] for upgrade in kepler_state["ship"]["upgrades"] if upgrade["availableHere"]}

    assert "fuel_tanks" in aurora_offers
    assert "jump_drive" not in aurora_offers
    assert "jump_drive" in kepler_offers
    assert aurora_offers != kepler_offers


def test_cheat_settings_are_public_and_toggleable():
    game = create_game()

    updated, message = apply_action(game, "set_cheat", {"cheat": "unlimitedFuel", "enabled": True})
    state = public_state(updated)
    fuel_cheat = next(cheat for cheat in state["cheats"] if cheat["id"] == "unlimitedFuel")

    assert "Unlimited fuel enabled" in message
    assert fuel_cheat["enabled"] is True
    assert state["status"] == "Cheats active"


def test_unlimited_fuel_allows_travel_without_consuming_fuel():
    game = create_game()
    game, _ = apply_action(game, "set_cheat", {"cheat": "unlimitedFuel", "enabled": True})
    game, _ = apply_action(game, "explore", {})
    game, _ = apply_action(game, "local_travel", {"movement": "undock"})
    game["fuel"] = 0

    updated, message = apply_action(game, "travel", {"destination": "kepler"})
    state = public_state(updated)

    assert "Unlimited fuel covered" in message
    assert updated["location"] == "kepler"
    assert state["fuel"] == state["maxFuel"]


def test_unlimited_credits_and_free_materials_allow_upgrade_without_resources():
    game = create_game()
    game["credits"] = 0
    game, _ = apply_action(game, "set_cheat", {"cheat": "unlimitedCredits", "enabled": True})
    game, _ = apply_action(game, "set_cheat", {"cheat": "freeMaterials", "enabled": True})

    upgraded, message = apply_action(game, "buy_upgrade", {"upgradeId": "fuel_tanks"})
    state = public_state(upgraded)

    assert "Auxiliary Fuel Tanks tier 1" in message
    assert upgraded["credits"] == 0
    assert upgraded["inventory"] == game["inventory"]
    assert state["maxFuel"] == 24


def test_invulnerable_hull_restores_hull_when_enabled():
    game = create_game()
    game["hull"] = 1

    updated, message = apply_action(game, "set_cheat", {"cheat": "invulnerableHull", "enabled": True})
    state = public_state(updated)

    assert "Invulnerable hull enabled" in message
    assert state["hull"] == state["maxHull"]


def test_ship_ai_profile_is_configured_once_and_locked():
    game = create_game()

    configured, message = apply_action(
        game,
        "configure_ship_ai",
        {
            "name": "Selene",
            "gender": "Male",
            "description": "Friendly, flirtatious, decisive, and protective when the ship is under pressure.",
        },
    )
    locked, locked_message = apply_action(
        configured,
        "configure_ship_ai",
        {
            "name": "Different",
            "gender": "Female",
            "description": "This should not overwrite the existing core profile.",
        },
    )
    state = public_state(locked)

    assert "Imprinted Selene" in message
    assert "locked" in locked_message
    assert state["shipAi"]["configured"] is True
    assert state["shipAi"]["name"] == "Selene"
    assert state["shipAi"]["gender"] == "Male"


def test_ship_ai_core_strip_is_costly_and_resets_to_blank_generation():
    game = create_game()
    configured, _ = apply_action(
        game,
        "configure_ship_ai",
        {
            "name": "Selene",
            "gender": "Female",
            "description": "Friendly, flirtatious, decisive, and protective when the ship is under pressure.",
        },
    )
    blocked, blocked_message = apply_action(configured, "strip_ship_ai", {})
    configured["credits"] = 5000

    stripped, message = apply_action(configured, "strip_ship_ai", {})
    state = public_state(stripped)

    assert "requires 5000 credits" in blocked_message
    assert blocked["ship_ai"]["configured"] is True
    assert "Stripped the old AI core" in message
    assert stripped["credits"] == 0
    assert state["shipAi"]["configured"] is False
    assert state["shipAi"]["generation"] == 2
    assert state["shipAi"]["name"] == "Peregrine Factory AI"
