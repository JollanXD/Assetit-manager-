# AssetIt Manager architecture

## Product direction

AssetIt is a local-first asset browser inspired by the approved AssetItUI reference. It does not require an account, sign-in, cloud service, or an internet connection for core workflows.

## Separate the replaceable UI from the core

- `ui/`: the React/TypeScript interface copied from the AssetItUI reference. UI releases should be replaceable without rewriting asset indexing or storage.
- `assetit_core/`: local library discovery, asset metadata, filtering/search primitives, tags, favorites, and settings persistence. This layer must not depend on React or Qt widgets.
- `main.py`: desktop launcher and host integration. It is responsible for launching the UI and exposing a small, versioned bridge to the core.
- `Plugins/`: reserved for future integrations installed into external DCC applications. These are not plugins that extend the AssetIt Manager itself.
- User data lives outside the application directory so portable app updates cannot overwrite libraries, preferences, or the index.

## Bridge contract

The UI communicates with the core using explicit requests and structured responses. Keep the contract versioned and small; never let UI components scan disks or modify files directly. Every file operation must be local, predictable, and initiated by the user.

Initial bridge capabilities:
- list/add/remove/rescan local library roots;
- query indexed assets and metadata;
- update tags and favorites;
- reveal an asset in the file manager;
- read and update application preferences.

## Development and release

The primary repository remains `JollanXD/Assetit-manager-`. `JollanXD/AssetItUI` is a design reference, not the production repository. The Windows portable package continues to be built by GitHub Actions.

## Implementation order

1. Establish the UI/core boundary and preserve the current portable build.
2. Bring the reference UI into the production repository with its layout and styling intact.
3. Replace demo data and simulated actions with the local core.
4. Verify offline behavior, persistence, and safe library rescanning.
5. Add DCC application integrations later, as a separate workstream.
