@domain:documentation-site @area:theme-palette @from:docs/stylesheets
Feature: Presenting the documentation in the project's own palette
  Gives docs readers one consistent green GreenOps look across the rendered docs and the splash page, without the pages loading anything over the network.

  Background:
    Given the documentation site is built with the project's theme stylesheet

  @id:documentation-site.theme-palette.001 @rule:docs.theme.greenops-accent-pair @inferred @source:docs/stylesheets/extra.css#:root @questionable
  Scenario: The docs use the green GreenOps accent pair
    Given the theme's accent pair is #34d399 and #059669
    When a reader opens any documentation page
    Then the header, tabs and links on a light background are shown in #059669
    And links on the dark scheme are shown in #34d399 on a #0b0f1a ground
    And primary buttons and the home-page title use a gradient from #34d399 to #059669

  @id:documentation-site.theme-palette.002 @rule:docs.theme.splash-shares-palette @inferred @source:docs/stylesheets/extra.css#:root
  Scenario: The splash page and the docs show the same accent colours
    Given the accent pair is defined only in the theme stylesheet
    When a reader moves from the splash page to the docs
    Then the splash page's install label and links use the same #059669 accent as the docs

  @id:documentation-site.theme-palette.003 @rule:docs.theme.no-network-assets @inferred @source:docs/stylesheets/extra.css#:root
  Scenario: Documentation pages load no fonts or styles from the network
    Given the reader's device has no internet access
    When a reader opens the documentation
    Then text is shown in the device's system sans-serif font
    And code is shown in the device's system monospace font
    And no web font, CDN asset or analytics script is requested

  @id:documentation-site.theme-palette.004 @rule:docs.theme.no-stand-in-logo @inferred @source:docs/stylesheets/extra.css#.md-header__button.md-logo
  Scenario: The docs header shows no placeholder logo
    Given the project has no logo configured
    When a reader opens any documentation page
    Then the header and navigation title show no logo icon
