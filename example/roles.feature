Feature: Roles Management

  @SCRUM-14 @AC1 @Automated_UI @UI_Functional_Test @RoleManagement
  Scenario: Show list of roles
    Given the user is logged
    When the user navigates on roles list page
    Then the system shows a table with role name and role description

  @SCRUM-15 @AC2 @Automated_UI @UI_Functional_Test @RoleManagement
  Scenario: Create a new role
    Given the user is logged
    When the user navigates on create role page
    Then the system allows to insert name and description
    And the system allows to save the new role

  @SCRUM-16 @AC3 @Automated_UI @UI_Functional_Test @RoleManagement
  Scenario: Update a role
    Given the user is logged
    When the user navigates on roles list page
    And the user selects a role
    Then the system allows to update name and description
    And the system allows to save the role updated

    @SCRUM-17 @AC4 @Automated_UI @UI_Functional_Test @RoleManagement
  Scenario: Delete a role
    Given the user is logged
    When the user navigates on roles list page
    And the user selects a role
    Then the system allows to delete the role