#!/bin/bash

# find . -type f -name "*.goal" -print0 | while IFS= read -r -d $'\0' file; do
#   echo "Validating: $file"
#   goaldsl validate "$file"
#   if [ $? -ne 0 ]; then
#     echo "Validation failed for: $file"
#   fi
# done

# find . -type f -name "*.goal" -not -path "./rse_scenarios*" -print0 | while IFS= read -r -d $'\0' file; do
#   echo "Validating: $file"
#   goaldsl validate "$file"
#   if [ $? -ne 0 ]; then
#     echo "Validation failed for: $file"
#   fi
# done

SUCCESS_COUNT=0
FAILURE_COUNT=0

while IFS= read -r -d $'\0' file; do
  echo -e "\e[34m[Processing]\e[0m Validating: \"$file\""
  goaldsl validate "$file"
  RESULT=$?
  if [ "$RESULT" -eq 0 ]; then
    echo -e "\e[32m[Success]\e[0m Validation successful for: \"$file\""
    ((SUCCESS_COUNT++))
  else
    echo -e "\e[31m[Failure]\e[0m Validation failed for: \"$file\" (Exit Code: $RESULT)"
    ((FAILURE_COUNT++))
  fi
done < <(find . -type f -name "*.goal" -not -path "./rse_scenarios*" -print0)

echo -e ""
echo -e "--------------------------------------------------"
echo -e "          \e[1mGoalDSL Validation Report\e[0m"
echo -e "--------------------------------------------------"
echo -e "  \e[32mSuccessful Validations:\e[0m $SUCCESS_COUNT"
echo -e "  \e[31mFailed Validations:\e[0m   $FAILURE_COUNT"
echo -e "--------------------------------------------------"

if [ "$FAILURE_COUNT" -gt 0 ]; then
  echo -e "\e[33m[Warning]\e[0m One or more validations encountered errors. Please review the individual validation messages for details."
else
  echo -e "\e[32m[Info]\e[0m All GoalDSL validations completed successfully."
fi
