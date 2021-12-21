<div>
  <h1 align="center">https-saleor-dev-local</h1>
  <h4 align="center">
    A fork from Saleor API to run on development environment. Includes fixtures,
    HTTP/S serving, and minimal setup guides.
  </h4>
</div>

## Environment Variables

Create a `common.env` file in the current directory and paste the following
contents:

```.env
DATABASE_URL=postgres://saleor:saleor@db/saleor
DEFAULT_FROM_EMAIL=noreply@example.com
CELERY_BROKER_URL=redis://redis:6379/1
SECRET_KEY=changeme
EMAIL_URL=smtp://mailhog:1025
ENABLE_ACCOUNT_CONFIRMATION_BY_EMAIL=1
ALLOWED_CLIENT_HOSTS=localhost,127.0.0.1
ALLOWED_HOSTS=localhost,127.0.0.1
```

> If you have any custom host append it to the `ALLOWED_CLIENT_HOSTS` and `ALLOWED_HOSTS` variables. Eg: `ALLOWED_HOSTS=localhost,127.0.0.1,example.com`

## Getting Started

> Make sure you follow [environment variables setup](#environment-variables).

1. Clone this repository `git clone https://github.com/EstebanBorai/https-saleor-dev-local.git`

2. Step onto the repository directory and run `docker-compose build`

3. Apply Django Migrations: `docker-compose run --rm api python3 manage.py migrate`

4. Collect static resources for Django: `docker-compose run --rm api python3 manage.py collectstatic --noinput`

6. Populate database and create a superuser: `docker-compose run --rm api python3 manage.py populatedb --createsuperuser` (Similar to seeding)

7. Spin it up: `docker-compose up`

## HTTP/S serving

This project uses `django-sslserver2` to serve under HTTPS in your local environment,
you must provide certificates under: `certificates` directory.

- `certificates/cert.pem`
- `certificates/key.pem`

Then update the `command` value for the `api` service in the _docker-compose.yml_
file:

```
command: python manage.py runsslserver --certificate certificates/cert.pem --key certificates/key.pem 0.0.0.0:8000
```

## GraphQL Playground

You can use the included GraphQL playground through http://localhost:8000/graphql/

```gql
mutation {
  tokenCreate(email: "admin@example.com", password: "admin") {
    token
  }
}
```

## Setting up emails

When running Saleor locally some steps must be done in order to have Emails
working locally. [Official Docs](https://docs.saleor.io/docs/3.0/developer/running-saleor/debugging-emails#local-development-environment).

As this repository only includes the Saleor API, the following guide will walk
you through setting up emails for local development.

1. Enable both: AdminEmails and UserEmails plugins by using the GraphQL server:

```gql
mutation {
  pluginUpdate(
  id: "mirumee.notifications.admin_email"
  input: {
    active: false,
  }
  ) {
    plugin {
      name,
      description
    }
    errors {
      field
      message
      code
    }
  }
}
```

```gql
mutation {
  pluginUpdate(
  id: "mirumee.notifications.user_email"
  channelId: <YOUR CHANNEL ID>
  input: {
    active: false,
  }
  ) {
    plugin {
      name,
      description
    }
    errors {
      field
      message
      code
    }
  }
}
```

2. Open your favorite database manager and bind it to local Saleor's database
instance. Then open the `plugins_pluginconfiguration` table. You must see at
least 2 rows which `identifier` colum's value is:

- `mirumee.notifications.user_email`
- `mirumee.notifications.admin_email`

3. Replace the `configuration` column value for each row using the corresponding
JSON configuration file available in this repository under `_fixtures/` directory.

- `admin_email_plugin_config.json`
- `user_email_plugin_config.json`

4. Validate configuration and activate plugin by performing the following
GraphQL mutations:

```gql
mutation {
  pluginUpdate(
  id: "mirumee.notifications.admin_email"
  input: {
    active: true,
  }
  ) {
    plugin {
      name,
      description
    }
    errors {
      field
      message
      code
    }
  }
}
```

```gql
mutation {
  pluginUpdate(
  id: "mirumee.notifications.user_email"
  channelId: <YOUR CHANNEL ID>
  input: {
    active: true,
  }
  ) {
    plugin {
      name,
      description
    }
    errors {
      field
      message
      code
    }
  }
}
```

Emails will be available on http://localhost:8025/ when sent through Saleor.

## Links of Interest

- Mailhog: http://localhost:8025/ [Config](https://github.com/mailhog/MailHog#configuration)
- GraphQL Playground: https://localhost:8000/graphql/

## Documentation (v3.0) Relevant Links

- https://docs.saleor.io/docs/3.0/developer/running-saleor/debugging-emails

## License

Disclaimer: Everything you see here is open and free to use as long as you comply with the [license](https://github.com/saleor/saleor/blob/master/LICENSE). There are no hidden charges. We promise to do our best to fix bugs and improve the code.

Some situations do call for extra code; we can cover exotic use cases or build you a custom e-commerce appliance.

#### Crafted with ❤️ by [Saleor Commerce](https://saleor.io)

hello@saleor.io
