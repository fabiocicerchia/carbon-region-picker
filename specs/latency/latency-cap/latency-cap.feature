@domain:latency @area:latency-cap @from:carbon-region-picker/carbon-region-picker
Feature: Constraining regions by latency
  Serves engineers with latency budgets, by dropping regions too far from where their users are.

  Background:
    Given Given the bundled round-trip estimates are in use

  @id:latency.latency-cap.001 @rule:latency.latency-cap.drop-over-cap @verified @source:carbon_region_picker.py#rank @test:tests/test_carbon_region_picker.py#test_latency_constraint_filters
  Scenario Outline: Regions slower than the cap from the chosen vantage point are dropped
    When the operator ranks aws regions near <near> with a latency cap of <cap> ms
    Then only <kept> are listed, in that order
    And no listed region has a latency above <cap>ms

    Examples:
      | near    | cap | kept                                           |
      | eu      | 40  | eu-north-1, eu-west-3, eu-west-1, eu-central-1 |
      | eu      | 35  | eu-north-1, eu-west-3, eu-west-1, eu-central-1 |
      | us-east | 30  | ca-central-1, us-east-1                        |

  @id:latency.latency-cap.002 @rule:latency.latency-cap.zero-means-uncapped @inferred @source:carbon_region_picker.py#rank @questionable
  Scenario: A latency cap of zero is treated as no cap at all
    When the operator ranks aws regions near eu with a latency cap of 0 ms
    Then all 9 aws regions are listed
    And the heading reads "# Regions by carbon intensity" with no constraint
