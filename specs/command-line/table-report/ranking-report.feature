@domain:command-line @area:table-report @from:carbon-region-picker/carbon-region-picker
Feature: Reading the ranking report
  Serves engineers reading the default Markdown output, which shows the constraint, flags clean grids and estimates the carbon saving.

  Background:
    Given the bundled yearly-average grid intensities are in use
    Andthe output format is the default table

  @id:command-line.table-report.001 @rule:command-line.table-report.constraint-heading @inferred @source:carbon_region_picker.py#render
  Scenario Outline: The heading states the latency constraint when one is set
    When the operator ranks aws regions near <near> with a latency cap of <cap>
    Then the heading reads "<heading>"
    And the table has the columns rank, region, gCO2e/kWh and latency

    Examples:
      | near    | cap  | heading                                            |
      | eu      | 60   | # Regions by carbon intensity (≤60ms from eu)      |
      | us-east | 30   | # Regions by carbon intensity (≤30ms from us-east) |
      | eu      | none | # Regions by carbon intensity                      |

  @id:command-line.table-report.002 @rule:region-ranking.clean-grid-marker.below-threshold @verified @source:carbon_region_picker.py#render @test:tests/test_carbon_region_picker.py#test_render_mentions_savings_factor
  Scenario Outline: Regions on a grid below 100 gCO2e/kWh are marked clean
    Given a ranked region has an intensity of <intensity> gCO2e/kWh
    When the operator views the ranking table
    Then that region's name is <shown>

    Examples:
      | intensity | shown           |
      | 25        | followed by 🌱   |
      | 99        | followed by 🌱   |
      | 100       | shown without 🌱 |
      | 120       | shown without 🌱 |

  @id:command-line.table-report.003 @rule:region-ranking.savings-estimate.best-over-worst-factor @verified @source:carbon_region_picker.py#render @test:tests/test_carbon_region_picker.py#test_render_mentions_savings_factor
  Scenario Outline: The report estimates how many times less carbon the best region emits than the worst
    Given no latency cap is set
    When the operator ranks <provider> regions near eu
    Then the report ends with "Picking `<best>` over `<worst>` cuts compute carbon ~<factor>x."

    Examples:
      | provider | best          | worst        | factor |
      | aws      | eu-north-1    | ap-south-1   | 26     |
      | gcp      | us-west1      | asia-south1  | 7      |
      | azure    | westus2       | centralindia | 7      |

  @id:command-line.table-report.004 @rule:region-ranking.savings-estimate.omitted-without-difference @inferred @source:carbon_region_picker.py#render
  Scenario Outline: No saving is claimed when every listed region is equally clean or none is listed
    Given the latency cap leaves <remaining>
    When the operator views the ranking table
    Then no "cuts compute carbon" line is shown
    And <table>

    Examples:
      | remaining       | table                           |
      | a single region | the table lists that one region |
      | no region       | the table shows only its header |
