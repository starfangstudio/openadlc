<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Android persistence (Room)

Room is the default local DB on Android. Treat the schema as a **versioned contract**: a shipped migration that loses user data is the worst Android bug class.

## Entities & DAOs
- `@Entity` data classes; explicit `@PrimaryKey`; index foreign keys (`@Index`). Keep DB models separate from domain/UI models, map at the repository boundary (see `android-architecture`).
- `@Dao` methods: `suspend` for one-shot reads/writes; return **`Flow<T>`** for observed queries (Room re-emits on change). Never block the main thread, Room rejects it unless `allowMainThreadQueries` (don't use it).
- `@Insert(onConflict = …)`, `@Update`, `@Delete`, `@Query` (SQL is compile-time-checked). `@Transaction` for multi-step reads/writes; `@Relation` for joins.
- `TypeConverter`s for enums/dates, keep them total (handle every value) and unit-test them.

## Migrations: the part that bites
- **Every schema change needs a `Migration(n → n+1)`** (or a tested `AutoMigration`); bump `version`. **Never** ship `fallbackToDestructiveMigration()` in release, it wipes user data.
- **Export the schema** (`room.schemaLocation`) and commit the JSON; it's the diff that proves what changed.
- **Test every migration** with `MigrationTestHelper`: create the DB at vN, run the migration, assert data + schema at vN+1. A migration without a test is unverified.

## Build / threading / DI
- Use **KSP** for the Room compiler (not KAPT); declare deps via the version catalog (see `android-build-gradle`).
- One DB instance, injected (`@SingleInstanceIn(AppScope::class)` / `@Singleton`); inject DAOs, don't `new` them. Run queries off the main thread via the project's `DispatcherProvider`.

## References
- Save data with Room: https://developer.android.com/training/data-storage/room
- Migrating Room DBs + `MigrationTestHelper`: https://developer.android.com/training/data-storage/room/migrating-db-versions
- Room with KSP: https://developer.android.com/build/migrate-to-ksp

## Note
Some codebases use Room with **RxJava2** in places (DAOs returning `Single`/`Observable` alongside coroutines) and **SQLCipher** for encrypted stores. Match the module's existing style rather than imposing coroutines/Flow everywhere.
