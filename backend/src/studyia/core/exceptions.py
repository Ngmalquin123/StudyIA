"""Errores de negocio. Los servicios los lanzan y las rutas los traducen a HTTP."""


class EmailAlreadyRegistered(Exception):
    pass


class RoleNotFound(Exception):
    pass


class InvalidCurrentPassword(Exception):
    pass
