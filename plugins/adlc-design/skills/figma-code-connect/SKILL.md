---
name: figma-code-connect
description: "This skill should be used to set up or maintain Figma Code Connect so designs map to real code components, \"set up Code Connect\", \"connect our components to Figma\", \"why is Figma generating new components instead of reusing ours\", \"map this Figma component to our code\", \"publish Code Connect\", or when figma-extract reports a Figma node with no code mapping. Authors and publishes the figma.connect files that link code components to Figma components, so the Figma MCP returns your real component for a node and the build reuses it instead of regenerating a one-off. Figma is the only supported design tool."
version: 0.1.0
---
<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->

# Figma Code Connect

Link your code components to their Figma components so design-to-code reuses what you already have. Without it, the AI regenerates a fresh component for every frame; with it, the Figma MCP returns your real component and the build reuses it. This is the backbone of reuse.

**Load on demand** for UI work, and especially when `figma-extract` reports a node with no Code Connect mapping. Requires Figma account access.

## Step 1: Detect what exists
Look for an existing setup: `*.figma.tsx` (or `.figma.swift` / Compose) connection files, `figma.config.json`, and `@figma/code-connect` in the deps. Record which components are already connected and which are not. Never duplicate an existing mapping.

## Step 2: Map precisely to the design system
Map each unconnected Figma component to its **canonical design-system component**, never to a local copy, fork, or one-off. Use the `design-system-audit` inventory to find the DS source of truth.
- author its connection file pointed at the DS component: `figma.connect(<DSComponent>, '<figma-node-url>', { props: { ... }, example: (props) => <DSComponent ... /> })`,
- map **precisely**: each Figma variant and property maps to the exact DS prop and value (1:1), so a design variant resolves to the right DS prop, never an approximation,
- one connection per component, co-located with the DS component.

If the design uses a component the DS does not have, that is a **DS gap**: flag it, do not map to a local hack. The component belongs in the design system first. Support the project's framework (React, SwiftUI, Jetpack Compose, HTML / web components). Mark any Figma property you cannot map `unknown`; do not invent a prop.

## Step 3: Validate locally
Run the parser (`figma connect parse`) to confirm the connection files compile and resolve. Fix errors at the source. Local, no approval needed.

## Step 4: Publish (outbound, needs the operator's explicit yes)
`figma connect publish` writes the mappings to Figma so Dev Mode and the MCP return them. **This is outbound and needs a Figma token: STOP and ask the operator for an explicit yes**, present what would publish, and read the token from the environment, never hardcode or fabricate a credential.

## Output
Published Code Connect mappings, so `get_code_connect_map` (used by `figma-extract` and `figma-implement`) returns the real code component for each connected node, and the build reuses instead of rebuilding.

## Outbound checkpoint
Detecting, authoring, and parsing connection files is local and needs no approval. `figma connect publish` (and any write to Figma) is outbound: get the operator's explicit yes first. The Figma access token is a credential, never commit or hardcode it.

## References
- Figma Code Connect docs: https://www.figma.com/code-connect-docs/
- Consumed by: `figma-extract`, `figma-implement`. Component inventory: `design-system-audit`.
