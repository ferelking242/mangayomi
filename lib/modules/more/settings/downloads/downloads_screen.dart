import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:watchtower/l10n/generated/app_localizations.dart';
import 'package:watchtower/modules/library/providers/file_scanner.dart';
import 'package:watchtower/modules/more/settings/downloads/providers/downloads_state_provider.dart';
import 'package:watchtower/providers/l10n_providers.dart';
import 'package:watchtower/services/download_manager/download_settings_service.dart';
import 'package:watchtower/utils/extensions/build_context_extensions.dart';
// ──────────────────────────────────────────────────────────────
// Main Screen
// ──────────────────────────────────────────────────────────────

class DownloadsScreen extends ConsumerStatefulWidget {
  const DownloadsScreen({super.key});

  @override
  ConsumerState<DownloadsScreen> createState() => _DownloadsScreenState();
}

class _DownloadsScreenState extends ConsumerState<DownloadsScreen> {
  @override
  void initState() {
    super.initState();
    DownloadSettingsService.instance.load();
  }

  @override
  Widget build(BuildContext context) {
    final saveAsCBZ = ref.watch(saveAsCBZArchiveStateProvider);
    final deleteAfterReading = ref.watch(deleteDownloadAfterReadingStateProvider);
    final onlyOnWifi = ref.watch(onlyOnWifiStateProvider);
    final concurrentDownloads = ref.watch(concurrentDownloadsStateProvider);
    final localFolders = ref.watch(localFoldersStateProvider);
    final downloadMode = ref.watch(downloadModeStateProvider);
    final archiveFormat = ref.watch(archiveFormatStateProvider);
    final concManga = ref.watch(concurrentMangaStateProvider);
    final concWatch = ref.watch(concurrentWatchStateProvider);
    final concNovel = ref.watch(concurrentNovelStateProvider);
    final swipeLeft = ref.watch(swipeLeftActionStateProvider);
    final swipeRight = ref.watch(swipeRightActionStateProvider);
    final l10n = l10nLocalizations(context);
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: Text(l10n!.downloads)),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [

            // ── Download Mode ──────────────────────────────
            _SectionHeader(title: 'Download Mode'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Container(
                decoration: BoxDecoration(
                  color: scheme.surfaceContainerHighest.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: scheme.outlineVariant.withOpacity(0.4)),
                ),
                child: Column(
                  children: DownloadMode.values.map((mode) {
                    final selected = downloadMode == mode;
                    final isLast = mode == DownloadMode.values.last;
                    return Column(
                      children: [
                        _CompactModeRow(
                          mode: mode,
                          selected: selected,
                          onTap: () => ref.read(downloadModeStateProvider.notifier).set(mode),
                        ),
                        if (!isLast)
                          Divider(height: 1, indent: 52, endIndent: 12,
                              color: scheme.outlineVariant.withOpacity(0.3)),
                      ],
                    );
                  }).toList(),
                ),
              ),
            ),

            // ── General ───────────────────────────────────
            _SectionHeader(title: 'General'),
            _SwitchRow(
              icon: Icons.wifi_outlined,
              title: l10n.only_on_wifi,
              value: onlyOnWifi,
              onChanged: (v) => ref.read(onlyOnWifiStateProvider.notifier).set(v),
            ),
            _SwitchRow(
              icon: Icons.delete_sweep_outlined,
              title: l10n.delete_download_after_reading,
              value: deleteAfterReading,
              onChanged: (v) => ref.read(deleteDownloadAfterReadingStateProvider.notifier).set(v),
            ),

            // Archive format
            _SectionHeader(title: 'Archive Format'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Container(
                decoration: BoxDecoration(
                  color: scheme.surfaceContainerHighest.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: scheme.outlineVariant.withOpacity(0.4)),
                ),
                child: Column(
                  children: ArchiveFormat.values.map((fmt) {
                    final selected = archiveFormat == fmt;
                    final isLast = fmt == ArchiveFormat.values.last;
                    return Column(
                      children: [
                        InkWell(
                          onTap: () => ref.read(archiveFormatStateProvider.notifier).set(fmt),
                          borderRadius: BorderRadius.circular(12),
                          child: Padding(
                            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                            child: Row(
                              children: [
                                Container(
                                  width: 32,
                                  height: 32,
                                  decoration: BoxDecoration(
                                    color: selected
                                        ? scheme.primary.withOpacity(0.15)
                                        : Colors.transparent,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Icon(
                                    fmt == ArchiveFormat.none
                                        ? Icons.folder_outlined
                                        : Icons.folder_zip_outlined,
                                    size: 18,
                                    color: selected ? scheme.primary : scheme.onSurfaceVariant,
                                  ),
                                ),
                                const SizedBox(width: 12),
                                Expanded(
                                  child: Text(fmt.label,
                                      style: TextStyle(
                                          fontSize: 14,
                                          fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
                                          color: selected ? scheme.primary : scheme.onSurface)),
                                ),
                                if (selected)
                                  Icon(Icons.check_rounded, size: 18, color: scheme.primary),
                              ],
                            ),
                          ),
                        ),
                        if (!isLast)
                          Divider(height: 1, indent: 52, endIndent: 12,
                              color: scheme.outlineVariant.withOpacity(0.3)),
                      ],
                    );
                  }).toList(),
                ),
              ),
            ),

            // ── Concurrent Downloads ───────────────────────
            _SectionHeader(title: 'Concurrent Downloads'),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Container(
                decoration: BoxDecoration(
                  color: scheme.surfaceContainerHighest.withOpacity(0.5),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: scheme.outlineVariant.withOpacity(0.4)),
                ),
                child: Column(
                  children: [
                    _ConcurrentRow(
                      icon: Icons.menu_book_outlined,
                      label: 'Manga',
                      value: concManga,
                      max: 30,
                      onChanged: (v) => ref.read(concurrentMangaStateProvider.notifier).set(v),
                      isFirst: true,
                    ),
                    Divider(height: 1, indent: 52, endIndent: 12,
                        color: scheme.outlineVariant.withOpacity(0.3)),
                    _ConcurrentRow(
                      icon: Icons.play_circle_outline_rounded,
                      label: 'Watch / Anime',
                      value: concWatch,
                      max: 10,
                      onChanged: (v) => ref.read(concurrentWatchStateProvider.notifier).set(v),
                    ),
                    Divider(height: 1, indent: 52, endIndent: 12,
                        color: scheme.outlineVariant.withOpacity(0.3)),
                    _ConcurrentRow(
                      icon: Icons.auto_stories_outlined,
                      label: 'Novel',
                      value: concNovel,
                      max: 30,
                      onChanged: (v) => ref.read(concurrentNovelStateProvider.notifier).set(v),
                      isLast: true,
                    ),
                  ],
                ),
              ),
            ),

            // ── Swipe Actions ─────────────────────────────
            _SectionHeader(title: 'Swipe Actions (Download Queue)'),
            _SwipeActionTile(
              label: 'Swipe Left',
              icon: Icons.swipe_left_outlined,
              current: swipeLeft,
              onChanged: (v) => ref.read(swipeLeftActionStateProvider.notifier).set(v),
            ),
            _SwipeActionTile(
              label: 'Swipe Right',
              icon: Icons.swipe_right_outlined,
              current: swipeRight,
              onChanged: (v) => ref.read(swipeRightActionStateProvider.notifier).set(v),
            ),

            // ── Local Folders ─────────────────────────────
            _SectionHeader(title: context.l10n.local_folder),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
              child: Row(
                children: [
                  Expanded(
                    child: _ActionButton(
                      icon: Icons.refresh_rounded,
                      label: context.l10n.rescan_local_folder,
                      onTap: () async => ref.read(scanLocalLibraryProvider.future),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _ActionButton(
                      icon: Icons.add_rounded,
                      label: context.l10n.add_local_folder,
                      onTap: () async {
                        final result = await FilePicker.getDirectoryPath();
                        if (result != null) {
                          final temp = localFolders.toList()..add(result);
                          ref.read(localFoldersStateProvider.notifier).set(temp);
                        }
                      },
                    ),
                  ),
                  const SizedBox(width: 10),
                  _ActionButton(
                    icon: Icons.help_outline_rounded,
                    label: 'Structure',
                    onTap: () => _showHelpDialog(context),
                    isPrimary: false,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  FutureBuilder(
                    future: getLocalLibrary(),
                    builder: (context, snapshot) => snapshot.data?.path != null
                        ? _FolderCard(
                            path: snapshot.data!.path,
                            isDefault: true,
                            onDelete: null,
                          )
                        : const SizedBox.shrink(),
                  ),
                  ...localFolders.map((e) => _FolderCard(
                    path: e,
                    isDefault: false,
                    onDelete: () {
                      final temp = localFolders.toList()..remove(e);
                      ref.read(localFoldersStateProvider.notifier).set(temp);
                    },
                  )),
                ],
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  void _showHelpDialog(BuildContext context) {
    final data = (
      "LocalFolder",
      [
        ("MangaName", [
          ("cover.jpg", Icons.image_outlined),
          ("Chapter1", [
            ("Page1.jpg", Icons.image_outlined),
            ("Page2.jpeg", Icons.image_outlined),
          ]),
          ("Chapter2.cbz", Icons.folder_zip_outlined),
        ]),
        ("AnimeName", [
          ("cover.jpg", Icons.image_outlined),
          ("Episode1.mp4", Icons.video_file_outlined),
          ("Episode1_subtitles", [("en.srt", Icons.subtitles_outlined)]),
        ]),
        ("NovelName", [
          ("cover.jpg", Icons.image_outlined),
          ("NovelName.epub", Icons.book_outlined),
        ]),
      ],
    );

    Widget buildSubFolder((String, dynamic) data, int level) {
      if (data.$2 is List) {
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text.rich(TextSpan(children: [
              for (int i = 1; i < level; i++) const WidgetSpan(child: SizedBox(width: 20)),
              if (level > 0) WidgetSpan(child: Icon(Icons.subdirectory_arrow_right)),
              WidgetSpan(child: Icon(Icons.folder)),
              const WidgetSpan(child: SizedBox(width: 5)),
              TextSpan(text: data.$1),
            ])),
            ...(data.$2 as List<(String, dynamic)>).map((e) => buildSubFolder(e, level + 1)),
          ],
        );
      }
      return Text.rich(TextSpan(children: [
        for (int i = 1; i < level; i++) const WidgetSpan(child: SizedBox(width: 20)),
        if (level > 0) WidgetSpan(child: Icon(Icons.subdirectory_arrow_right)),
        WidgetSpan(child: Icon(data.$2 as IconData)),
        const WidgetSpan(child: SizedBox(width: 5)),
        TextSpan(text: data.$1),
      ]));
    }

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(context.l10n.local_folder_structure),
        content: SizedBox(
          width: context.width(0.6),
          height: context.height(0.8),
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(8),
              child: buildSubFolder(data, 0),
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text(context.l10n.cancel),
          ),
        ],
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────
// Compact mode row (replaces big card)
// ──────────────────────────────────────────────────────────────

class _CompactModeRow extends StatelessWidget {
  final DownloadMode mode;
  final bool selected;
  final VoidCallback onTap;

  static const _icons = {
    DownloadMode.internalDownloader: Icons.download_outlined,
    DownloadMode.fkFallbackZeus: Icons.auto_fix_high_outlined,
    DownloadMode.zeusDl: Icons.bolt_outlined,
    DownloadMode.auto: Icons.smart_toy_outlined,
  };

  const _CompactModeRow({required this.mode, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Container(
              width: 32,
              height: 32,
              decoration: BoxDecoration(
                color: selected ? scheme.primary.withOpacity(0.15) : Colors.transparent,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Icon(_icons[mode] ?? Icons.download_outlined,
                  size: 18,
                  color: selected ? scheme.primary : scheme.onSurfaceVariant),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Text(mode.label,
                          style: TextStyle(
                              fontSize: 14,
                              fontWeight: selected ? FontWeight.w600 : FontWeight.normal,
                              color: selected ? scheme.primary : scheme.onSurface)),
                      if (mode == DownloadMode.fkFallbackZeus) ...[
                        const SizedBox(width: 6),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                          decoration: BoxDecoration(
                            color: scheme.primary.withOpacity(0.12),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text('Default',
                              style: TextStyle(fontSize: 10, color: scheme.primary,
                                  fontWeight: FontWeight.w600)),
                        ),
                      ],
                    ],
                  ),
                  const SizedBox(height: 1),
                  Text(mode.description,
                      style: TextStyle(fontSize: 11, color: scheme.onSurfaceVariant)),
                ],
              ),
            ),
            if (selected)
              Icon(Icons.check_rounded, size: 18, color: scheme.primary),
          ],
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────
// Concurrent slider row
// ──────────────────────────────────────────────────────────────

class _ConcurrentRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final int value;
  final int max;
  final void Function(int) onChanged;
  final bool isFirst;
  final bool isLast;

  const _ConcurrentRow({
    required this.icon,
    required this.label,
    required this.value,
    required this.max,
    required this.onChanged,
    this.isFirst = false,
    this.isLast = false,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(
        children: [
          Icon(icon, size: 20, color: scheme.onSurfaceVariant),
          const SizedBox(width: 12),
          SizedBox(
            width: 90,
            child: Text(label,
                style: TextStyle(fontSize: 14, color: scheme.onSurface)),
          ),
          Expanded(
            child: SliderTheme(
              data: SliderTheme.of(context).copyWith(
                trackHeight: 3,
                thumbShape: const RoundSliderThumbShape(enabledThumbRadius: 7),
                overlayShape: const RoundSliderOverlayShape(overlayRadius: 14),
              ),
              child: Slider(
                value: value.toDouble(),
                min: 1,
                max: max.toDouble(),
                divisions: max - 1,
                onChanged: (v) => onChanged(v.round()),
              ),
            ),
          ),
          Container(
            width: 30,
            alignment: Alignment.center,
            child: Text(
              '$value',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: scheme.primary),
            ),
          ),
        ],
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────
// Switch row
// ──────────────────────────────────────────────────────────────

class _SwitchRow extends StatelessWidget {
  final IconData icon;
  final String title;
  final bool value;
  final void Function(bool) onChanged;

  const _SwitchRow({
    required this.icon,
    required this.title,
    required this.value,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return InkWell(
      onTap: () => onChanged(!value),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            Icon(icon, size: 20, color: scheme.onSurfaceVariant),
            const SizedBox(width: 16),
            Expanded(child: Text(title, style: const TextStyle(fontSize: 14))),
            Switch(value: value, onChanged: onChanged),
          ],
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────
// Local folder card — redesigned
// ──────────────────────────────────────────────────────────────

class _FolderCard extends StatelessWidget {
  final String path;
  final bool isDefault;
  final VoidCallback? onDelete;

  const _FolderCard({required this.path, required this.isDefault, required this.onDelete});

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: scheme.surfaceContainerHighest.withOpacity(0.5),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isDefault
              ? scheme.primary.withOpacity(0.4)
              : scheme.outlineVariant.withOpacity(0.4),
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Icon(Icons.folder_rounded,
                color: isDefault ? scheme.primary : scheme.onSurfaceVariant, size: 20),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (isDefault)
                    Container(
                      margin: const EdgeInsets.only(bottom: 3),
                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                      decoration: BoxDecoration(
                        color: scheme.primary.withOpacity(0.12),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text('Default',
                          style: TextStyle(fontSize: 10, color: scheme.primary,
                              fontWeight: FontWeight.w600)),
                    ),
                  Text(path,
                      style: TextStyle(fontSize: 12, color: scheme.onSurfaceVariant),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis),
                ],
              ),
            ),
            if (!isDefault)
              IconButton(
                icon: Icon(Icons.delete_outline_rounded, size: 18, color: scheme.error),
                tooltip: 'Remove',
                onPressed: () => showDialog(
                  context: context,
                  builder: (_) => AlertDialog(
                    title: const Text('Remove folder'),
                    content: Text(path),
                    actions: [
                      TextButton(onPressed: () => Navigator.pop(context),
                          child: const Text('Cancel')),
                      TextButton(
                          onPressed: () {
                            Navigator.pop(context);
                            onDelete?.call();
                          },
                          child: Text('Remove', style: TextStyle(color: scheme.error))),
                    ],
                  ),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────
// Action button
// ──────────────────────────────────────────────────────────────

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  final bool isPrimary;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
    this.isPrimary = true,
  });

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(10),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        decoration: BoxDecoration(
          color: isPrimary
              ? scheme.primary.withOpacity(0.1)
              : scheme.surfaceContainerHighest.withOpacity(0.6),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(
            color: isPrimary
                ? scheme.primary.withOpacity(0.3)
                : scheme.outlineVariant.withOpacity(0.4),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 16,
                color: isPrimary ? scheme.primary : scheme.onSurfaceVariant),
            const SizedBox(width: 6),
            Text(label,
                style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                    color: isPrimary ? scheme.primary : scheme.onSurfaceVariant)),
          ],
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────
// Section header
// ──────────────────────────────────────────────────────────────

class _SectionHeader extends StatelessWidget {
  final String title;
  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 24, 16, 6),
      child: Text(
        title.toUpperCase(),
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: Theme.of(context).colorScheme.primary,
          letterSpacing: 1.0,
        ),
      ),
    );
  }
}

// ──────────────────────────────────────────────────────────────
// Swipe action tile
// ──────────────────────────────────────────────────────────────

class _SwipeActionTile extends StatelessWidget {
  final String label;
  final IconData icon;
  final SwipeAction current;
  final void Function(SwipeAction) onChanged;

  const _SwipeActionTile({
    required this.label,
    required this.icon,
    required this.current,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(label),
      subtitle: Text(current.label,
          style: TextStyle(fontSize: 12, color: context.secondaryColor)),
      trailing: const Icon(Icons.chevron_right),
      onTap: () {
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: Text(label),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: SwipeAction.values.map((action) {
                return RadioListTile<SwipeAction>(
                  title: Text(action.label),
                  value: action,
                  groupValue: current,
                  onChanged: (v) {
                    if (v != null) {
                      onChanged(v);
                      Navigator.pop(ctx);
                    }
                  },
                );
              }).toList(),
            ),
          ),
        );
      },
    );
  }
}
