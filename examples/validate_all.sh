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

find . -type f -name "*.goal" -not -path "./rse_scenarios*" -print0 | while IFS= read -r -d $'\0' file; do
  echo "Validating: $file"
  goaldsl validate "$file"
  RESULT=$?
  if [ $RESULT -eq 0 ]; then
    echo "Validation successful for: $file"
    ((SUCCESS_COUNT++))
  else
    echo "Validation failed for: $file (Exit code: $RESULT)"
    ((FAILURE_COUNT++))
  fi
done

echo ""
echo "----------------------"
echo "Validation Summary:"
echo "----------------------"
echo "Successful validations: $SUCCESS_COUNT"
echo "Failed validations: $FAILURE_COUNT"

if [ "$FAILURE_COUNT" -gt 0 ]; then
  echo "Warning: Some validations failed."
fi
