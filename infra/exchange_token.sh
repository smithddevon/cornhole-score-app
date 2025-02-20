echo "GITLAB_OIDC_TOKEN: ${GITLAB_OIDC_TOKEN}"

RESPONSE=$(curl -v -X POST "https://sts.googleapis.com/v1/token" \
  --header "Accept: application/json" \
  --header "Content-Type: application/json" \
  --data "${PAYLOAD}" \
)

echo "Response: ${RESPONSE}"