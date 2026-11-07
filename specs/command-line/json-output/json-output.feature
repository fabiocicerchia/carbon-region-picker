@domain:command-line @area:json-output @from:carbon-region-picker/carbon-region-picker
Feature: Machine-readable ranking
  Serves scripts and pipelines consuming the ranking, which rely on a stable JSON shape.

  Background:
    Giventhe operator asks for JSON output

  @id:command-line.json-output.001 @rule:command-line.json-output.region-records @verified @source:carbon_region_picker.py#emit @test:tests/test_carbon_region_picker.py#test_json_output_is_valid @test:tests/test_carbon_region_picker.py#test_gcp_and_azure_region_sets
  Scenario: The ranking is emitted as a list of region records
    Given no forecast is requested
    When the operator ranks aws regions near eu
    Then stdout is a JSON array in ranking order
    And each item has the keys region, zone, gco2_kwh and latency_ms in that order
    And the first item is {"region": "eu-north-1", "zone": "SE", "gco2_kwh": 25.0, "latency_ms": 35.0}

  @id:command-line.json-output.002 @rule:command-line.json-output.forecast-wraps-ranking @inferred @source:carbon_region_picker.py#emit @questionable
  Scenario Outline: A found cleanest hour turns the output into an object with the ranking and the slot
    Given live data with the cleanest-hour forecast is requested
    And <forecast>
    When the operator ranks aws regions near eu
    Then stdout is <shape>

    Examples:
      | forecast                                    | shape                                                                                   |
      | the top region's forecast has a lowest slot | an object with "regions" holding the records and "best_forecast_slot" holding that slot |
      | no forecast is available                    | a plain JSON array of the records                                                       |
