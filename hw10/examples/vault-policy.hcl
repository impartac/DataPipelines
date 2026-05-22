path "secret/data/production/my-app/*" {
  capabilities = ["read"]
}

path "secret/data/shared/*" {
  capabilities = ["read"]
}

path "database/creds/my-app-role" {
  capabilities = ["read"]
}


path "sys/leases/renew" {
  capabilities = ["update"]
}

path "sys/leases/revoke" {
  capabilities = ["update"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}
