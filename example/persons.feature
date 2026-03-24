Feature: Person Management

  @SCRUM-7 @AC1 @Automated_UI @WIP @Draft
  Scenario: Show list of persons
    Given the user is logged
    When the user navigates on persons list page
    Then the system shows a table with column name and column surname

  @SCRUM-8 @AC2 @Automated_UI @WIP @Draft
  Scenario: Create a new person
    Given the user is logged
    When the user navigates on create person page
    Then the system allows to insert name and surname
    And the system allows to save the new person
