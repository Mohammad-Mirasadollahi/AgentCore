# Naming And Boundary Rules

## Purpose

This document defines naming and boundary rules for `/root/AgentCore/backend`.

## Folder Naming

- Use lowercase kebab-case.
- Use explicit names that describe ownership.
- Use `-service` for backend services.
- Use provider names only under `integrations/`.
- Use stable test category names under `tests/`.

## Boundary Naming

Every boundary should answer:

- What does this module own?
- Which public contracts does it expose?
- Which modules may call it?
- Which modules may not call it?
- Which data does it own?
- Which configuration controls it?

## Forbidden Names

Avoid:

- common.
- shared without a clear contract.
- misc.
- utils.
- helpers.
- temp.
- old.
- new.
- experiments in production module paths.

Experimental work should live under an explicit experimental path only after approval.

## Dependency Naming

Imports and package names should make direction obvious. Domain code should not import infrastructure packages. Shared packages must not import services.
