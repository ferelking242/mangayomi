import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:watchtower/models/manga.dart';

/// AnymeX-style discovery tab header used by Watch, Manga and Novel tabs.
/// LEFT  — 3-D gradient account icon that opens a bottom sheet + greeting text
/// RIGHT — search icon

class LibraryHeaderBar extends StatelessWidget {
  final ItemType itemType;
  const LibraryHeaderBar({super.key, this.itemType = ItemType.anime});

  void _showAccountSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Theme.of(context).colorScheme.surface,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(28)),
      ),
      builder: (_) => const _AccountSheet(),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 6, 12, 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // ── Account 3-D button ──────────────────────────────────────────
          _Account3DButton(onTap: () => _showAccountSheet(context)),
          const SizedBox(width: 12),

          // ── Greeting ────────────────────────────────────────────────────
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  'Hey, Guest 👋',
                  style: TextStyle(
                    fontSize: 14.5,
                    fontWeight: FontWeight.w800,
                    color: cs.onSurface,
                    letterSpacing: -0.2,
                  ),
                ),
                Text(
                  "What are we doing today?",
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w500,
                    color: cs.onSurface.withValues(alpha: 0.50),
                  ),
                ),
              ],
            ),
          ),

          // ── Search ──────────────────────────────────────────────────────
          _SearchButton(
            onTap: () => context.push('/globalSearch',
                extra: (null as String?, itemType)),
          ),
        ],
      ),
    );
  }
}

// ── 3-D gradient account button ───────────────────────────────────────────────

class _Account3DButton extends StatelessWidget {
  final VoidCallback onTap;
  const _Account3DButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(999),
        child: Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                cs.primary.withValues(alpha: 0.90),
                cs.tertiary.withValues(alpha: 0.85),
                cs.secondary.withValues(alpha: 0.85),
              ],
            ),
            boxShadow: [
              BoxShadow(
                color: cs.primary.withValues(alpha: 0.32),
                blurRadius: 10,
                offset: const Offset(0, 4),
              ),
            ],
            border: Border.all(
              color: Colors.white.withValues(alpha: 0.22),
              width: 1.2,
            ),
          ),
          child: Stack(
            alignment: Alignment.center,
            children: [
              Positioned(
                top: 4,
                left: 6,
                right: 6,
                child: Container(
                  height: 9,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(999),
                    gradient: LinearGradient(
                      begin: Alignment.topCenter,
                      end: Alignment.bottomCenter,
                      colors: [
                        Colors.white.withValues(alpha: 0.40),
                        Colors.white.withValues(alpha: 0.0),
                      ],
                    ),
                  ),
                ),
              ),
              const Icon(Icons.person_rounded, color: Colors.white, size: 20),
            ],
          ),
        ),
      ),
    );
  }
}

// ── Search button ─────────────────────────────────────────────────────────────

class _SearchButton extends StatelessWidget {
  final VoidCallback onTap;
  const _SearchButton({required this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(14),
        child: Container(
          width: 42,
          height: 42,
          decoration: BoxDecoration(
            color: cs.surfaceContainerHighest.withValues(alpha: 0.7),
            borderRadius: BorderRadius.circular(14),
            border: Border.all(
              color: cs.outline.withValues(alpha: 0.18),
            ),
          ),
          child: Icon(Icons.search_rounded, color: cs.onSurface, size: 22),
        ),
      ),
    );
  }
}

// ── Account bottom sheet ──────────────────────────────────────────────────────

class _AccountSheet extends StatelessWidget {
  const _AccountSheet();

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final tt = Theme.of(context).textTheme;

    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 16, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 38,
                height: 4,
                decoration: BoxDecoration(
                  color: cs.onSurface.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Container(
                  width: 54,
                  height: 54,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: LinearGradient(
                      colors: [cs.primary, cs.tertiary],
                    ),
                  ),
                  child: const Icon(Icons.person_rounded,
                      color: Colors.white, size: 28),
                ),
                const SizedBox(width: 14),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Guest',
                        style: tt.titleMedium
                            ?.copyWith(fontWeight: FontWeight.w800)),
                    Text('Connect a tracker to sync your lists',
                        style: tt.bodySmall?.copyWith(
                            color: cs.onSurface.withValues(alpha: 0.55))),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 20),
            Divider(color: cs.outlineVariant.withValues(alpha: 0.5)),
            const SizedBox(height: 4),
            _SheetTile(
              icon: Icons.settings_outlined,
              label: 'Settings',
              onTap: () {
                Navigator.pop(context);
                context.push('/more');
              },
            ),
            _SheetTile(
              icon: Icons.track_changes_outlined,
              label: 'Tracking',
              onTap: () {
                Navigator.pop(context);
                context.push('/trackerLibrary');
              },
            ),
            _SheetTile(
              icon: Icons.history_outlined,
              label: 'History',
              onTap: () {
                Navigator.pop(context);
                context.push('/history');
              },
            ),
            _SheetTile(
              icon: Icons.info_outline_rounded,
              label: 'About',
              onTap: () {
                Navigator.pop(context);
                context.push('/more');
              },
            ),
          ],
        ),
      ),
    );
  }
}

class _SheetTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _SheetTile(
      {required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 4),
      leading: Container(
        width: 38,
        height: 38,
        decoration: BoxDecoration(
          color: cs.primaryContainer.withValues(alpha: 0.5),
          borderRadius: BorderRadius.circular(10),
        ),
        child: Icon(icon, color: cs.primary, size: 20),
      ),
      title: Text(label,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
      trailing: Icon(Icons.chevron_right_rounded,
          color: cs.onSurface.withValues(alpha: 0.35)),
      onTap: onTap,
    );
  }
}
