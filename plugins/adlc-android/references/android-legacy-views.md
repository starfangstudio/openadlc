<!-- SPDX-License-Identifier: LicenseRef-OpenADLC-Source-Available-1.0 -->
# Android legacy Views

Patterns for the View/XML system that still backs most production screens. Match whatever the target module already uses; do not introduce Compose into a pure-View module without consent.

## ViewBinding (replace findViewById)

Enable per module, never module-wide unless asked:
```kotlin
android { buildFeatures { viewBinding = true } }
```
Generated class name = layout file in PascalCase + `Binding` (`fragment_profile.xml` → `FragmentProfileBinding`).

- Activity: `binding = ActivityMainBinding.inflate(layoutInflater)`, then `setContentView(binding.root)`. Hold in a `val` field.
- Prefer ViewBinding over Kotlin synthetics (removed) and over DataBinding unless the module already commits to DataBinding's two-way binding/observability.

## Fragment ViewBinding: the leak gate

**CRITICAL: a Fragment outlives its View.** A field holding the binding leaks the entire view tree after `onDestroyView`. Always use the nullable-backing-property pattern and clear it:
```kotlin
private var _binding: FragmentProfileBinding? = null
private val binding get() = _binding!! // valid only between onCreateView and onDestroyView

override fun onCreateView(i: LayoutInflater, c: ViewGroup?, s: Bundle?): View {
    _binding = FragmentProfileBinding.inflate(i, c, false)
    return binding.root
}

override fun onDestroyView() {
    super.onDestroyView()
    _binding = null // mandatory, omitting this is a memory leak
}
```
Never access `binding` outside `onCreateView`..`onDestroyView` (e.g. in a callback that may fire after view teardown).

## Fragment navigation (Navigation component)

- Navigate via generated directions: `findNavController().navigate(ProfileFragmentDirections.toDetail(id))`. Do not manual-`FragmentTransaction` when a nav graph exists.
- Pass data with **Safe Args** (typed args), not loose `Bundle` keys. No parcelizing large objects, pass an id and re-fetch.
- Read args with `by navArgs<DetailFragmentArgs>()`.
- One `NavHostFragment` per nav graph; back-stack handled by the component, don't reimplement.

## RecyclerView: always ListAdapter + DiffUtil

Prefer `ListAdapter` over raw `RecyclerView.Adapter`: it runs DiffUtil off the main thread and animates changes. Never call `notifyDataSetChanged()` when a diff is possible.
```kotlin
class ItemAdapter : ListAdapter<Item, ItemAdapter.VH>(DIFF) {
    class VH(val b: ItemRowBinding) : RecyclerView.ViewHolder(b.root)

    override fun onCreateViewHolder(p: ViewGroup, vt: Int) =
        VH(ItemRowBinding.inflate(LayoutInflater.from(p.context), p, false))

    override fun onBindViewHolder(h: VH, pos: Int) { /* bind getItem(pos) */ }

    companion object {
        val DIFF = object : DiffUtil.ItemCallback<Item>() {
            override fun areItemsTheSame(a: Item, b: Item) = a.id == b.id        // identity
            override fun areContentsTheSame(a: Item, b: Item) = a == b           // visible content
        }
    }
}
```
- Push updates with `adapter.submitList(newList)`: pass a **new list instance** (DiffUtil compares references for the fast path); mutating in place is a silent no-op.
- `areItemsTheSame` = stable identity; `areContentsTheSame` = rendered equality (data classes make this free). Wrong split = wrong/janky animations.
- Set `setHasStableIds`/click listeners on the ViewHolder, not per-bind lambdas that re-allocate.

## Compose interop

Use interop only to migrate incrementally or wrap a component the other world lacks, not as a default.

### Compose inside a View/Fragment, `ComposeView`
```kotlin
binding.composeView.apply {
    setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed) // Fragments
    setContent { MaterialTheme { /* composable */ } }
}
```
- **Fragments → `DisposeOnViewTreeLifecycleDestroyed`** (ties Composition to the View lifecycle, avoids leaks/state loss).
- **RecyclerView item → `DisposeOnDetachedFromWindowOrReleasedFromPool`** (the default; pooling-aware).
- Multiple `ComposeView`s in one layout each need a **unique `id`** or `savedInstanceState` collides.

### View inside Compose: `AndroidView`
```kotlin
AndroidView(factory = { ctx -> LegacyChart(ctx) }, update = { it.setData(data) })
```
- `factory` runs once; `update` re-runs on recomposition when read state changes. Keep `factory` side-effect-free.
- Wrap a View only for a missing SDK component (MapView, AdView, custom canvas view); rewrite custom Views in Compose where feasible.

## References
- View binding: https://developer.android.com/topic/libraries/view-binding
- Using Compose in Views (ViewCompositionStrategy), https://developer.android.com/develop/ui/compose/migrate/interoperability-apis/compose-in-views
- DiffUtil / ListAdapter: https://developer.android.com/reference/androidx/recyclerview/widget/DiffUtil
- Navigation Safe Args: https://developer.android.com/guide/navigation/use-graph/pass-data
