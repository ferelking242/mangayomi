import 'dart:ui';
import 'package:extended_image/extended_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:watchtower/models/manga.dart';
import 'package:watchtower/modules/home/services/anilist_discovery_service.dart';

/// Full-screen AnymeX-style detail view for an [AnilistMedia] item.
/// Shows immediate data from the passed media object, then enriches
/// with characters / relations / studios via a live GraphQL fetch.
class AnilistDetailScreen extends ConsumerStatefulWidget {
  final AnilistMedia media;
  const AnilistDetailScreen({super.key, required this.media});

  @override
  ConsumerState<AnilistDetailScreen> createState() =>
      _AnilistDetailScreenState();
}

class _AnilistDetailScreenState extends ConsumerState<AnilistDetailScreen> {
  bool _descExpanded = false;

  // ── helpers ─────────────────────────────────────────────────────────────────

  String _formatStatus(String? s) {
    if (s == null) return '—';
    return switch (s) {
      'FINISHED' => 'Finished',
      'RELEASING' => 'Releasing',
      'NOT_YET_RELEASED' => 'Coming Soon',
      'CANCELLED' => 'Cancelled',
      'HIATUS' => 'On Hiatus',
      _ => s,
    };
  }

  String _formatSeason(String? season, int? year) {
    if (season == null && year == null) return '—';
    final s = season != null
        ? '${season[0]}${season.substring(1).toLowerCase()}'
        : '';
    return [s, if (year != null) year.toString()]
        .where((e) => e.isNotEmpty)
        .join(' ');
  }

  String _formatSource(String? s) {
    if (s == null) return '—';
    return s.replaceAll('_', ' ').split(' ').map((w) {
      if (w.isEmpty) return w;
      return '${w[0].toUpperCase()}${w.substring(1).toLowerCase()}';
    }).join(' ');
  }

  String _friendlyRelationType(String? r) {
    if (r == null) return '';
    return switch (r) {
      'SEQUEL' => 'Sequel',
      'PREQUEL' => 'Prequel',
      'PARENT' => 'Parent',
      'SIDE_STORY' => 'Side Story',
      'CHARACTER' => 'Character',
      'SUMMARY' => 'Summary',
      'ALTERNATIVE' => 'Alternative',
      'SPIN_OFF' => 'Spin-off',
      'OTHER' => 'Other',
      'SOURCE' => 'Source',
      'COMPILATION' => 'Compilation',
      'CONTAINS' => 'Contains',
      'ADAPTATION' => 'Adaptation',
      _ => r,
    };
  }

  // ── build ────────────────────────────────────────────────────────────────────

  @override
  Widget build(BuildContext context) {
    final m = widget.media;
    final detail = ref.watch(anilistMediaDetailProvider(m.id));
    final theme = Theme.of(context);
    final cs = theme.colorScheme;
    final banner = m.bannerImage ?? m.bestCover;

    return Scaffold(
      backgroundColor: theme.scaffoldBackgroundColor,
      body: Stack(
        children: [
          // ── Blurred background ──────────────────────────────────────────
          if (banner != null)
            Positioned.fill(
              child: ImageFiltered(
                imageFilter: ImageFilter.blur(sigmaX: 30, sigmaY: 30),
                child: ExtendedImage.network(
                  banner,
                  fit: BoxFit.cover,
                  cache: true,
                ),
              ),
            ),
          Positioned.fill(
            child: Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.black.withValues(alpha: 0.55),
                    theme.scaffoldBackgroundColor.withValues(alpha: 0.95),
                    theme.scaffoldBackgroundColor,
                  ],
                  stops: const [0.0, 0.45, 1.0],
                ),
              ),
            ),
          ),

          // ── Content ─────────────────────────────────────────────────────
          SafeArea(
            child: CustomScrollView(
              physics: const BouncingScrollPhysics(),
              slivers: [
                // ── Nav bar ────────────────────────────────────────────────
                SliverToBoxAdapter(
                  child: Padding(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                    child: Row(
                      children: [
                        _CircleBtn(
                          icon: Icons.arrow_back_rounded,
                          onTap: () => Navigator.of(context).maybePop(),
                        ),
                        const Spacer(),
                        _CircleBtn(
                          icon: Icons.open_in_browser_rounded,
                          onTap: () {
                            final url =
                                'https://anilist.co/${m.type.toLowerCase()}/${m.id}';
                            launchUrl(Uri.parse(url),
                                mode: LaunchMode.externalApplication);
                          },
                        ),
                      ],
                    ),
                  ),
                ),

                // ── Hero: cover + title ────────────────────────────────────
                SliverToBoxAdapter(
                  child: Padding(
                    padding:
                        const EdgeInsets.fromLTRB(20, 0, 20, 0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        // cover poster
                        Container(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(16),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.45),
                                blurRadius: 20,
                                offset: const Offset(0, 8),
                              ),
                            ],
                          ),
                          child: ClipRRect(
                            borderRadius: BorderRadius.circular(16),
                            child: SizedBox(
                              width: 110,
                              height: 160,
                              child: m.bestCover != null
                                  ? ExtendedImage.network(
                                      m.bestCover!,
                                      fit: BoxFit.cover,
                                      cache: true,
                                    )
                                  : Container(
                                      color: cs.surfaceContainerHighest,
                                      child: const Icon(
                                          Icons.image_not_supported_outlined),
                                    ),
                            ),
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              // type + score badges
                              Row(
                                children: [
                                  _TypeBadge(m.type, m.format,
                                      m.countryOfOrigin),
                                  if (m.averageScore != null) ...[
                                    const SizedBox(width: 8),
                                    _ScorePill(m.averageScore!),
                                  ],
                                ],
                              ),
                              const SizedBox(height: 8),
                              Text(
                                m.displayTitle,
                                style: theme.textTheme.titleLarge?.copyWith(
                                  fontWeight: FontWeight.w800,
                                  height: 1.2,
                                ),
                                maxLines: 3,
                                overflow: TextOverflow.ellipsis,
                              ),
                              if (m.titleRomaji != null &&
                                  m.titleRomaji != m.displayTitle) ...[
                                const SizedBox(height: 4),
                                Text(
                                  m.titleRomaji!,
                                  style: theme.textTheme.bodySmall?.copyWith(
                                    color: cs.onSurface.withValues(alpha: 0.55),
                                  ),
                                  maxLines: 1,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),

                const SliverToBoxAdapter(child: SizedBox(height: 20)),

                // ── Action buttons ─────────────────────────────────────────
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: Row(
                      children: [
                        Expanded(
                          child: _ActionBtn(
                            icon: Icons.collections_bookmark_outlined,
                            label: 'Add to Library',
                            primary: true,
                            onTap: () {
                              final type = m.type == 'MANGA'
                                  ? ItemType.manga
                                  : ItemType.anime;
                              context.push('/globalSearch',
                                  extra: (m.displayTitle, type));
                            },
                          ),
                        ),
                        const SizedBox(width: 12),
                        _ActionBtn(
                          icon: Icons.share_outlined,
                          label: null,
                          width: 52,
                          onTap: () {
                            final url =
                                'https://anilist.co/${m.type.toLowerCase()}/${m.id}';
                            launchUrl(Uri.parse(url),
                                mode: LaunchMode.externalApplication);
                          },
                        ),
                      ],
                    ),
                  ),
                ),

                const SliverToBoxAdapter(child: SizedBox(height: 20)),

                // ── Genre chips ────────────────────────────────────────────
                if (m.genres.isNotEmpty)
                  SliverToBoxAdapter(
                    child: SizedBox(
                      height: 36,
                      child: ListView.separated(
                        scrollDirection: Axis.horizontal,
                        padding:
                            const EdgeInsets.symmetric(horizontal: 20),
                        itemCount: m.genres.length,
                        separatorBuilder: (_, __) =>
                            const SizedBox(width: 8),
                        itemBuilder: (_, i) => _GenreChip(m.genres[i]),
                      ),
                    ),
                  ),

                if (m.genres.isNotEmpty)
                  const SliverToBoxAdapter(child: SizedBox(height: 20)),

                // ── Description ────────────────────────────────────────────
                if (m.description != null && m.description!.isNotEmpty)
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      child: _GlassCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _SectionTitle(
                              icon: Icons.description_outlined,
                              label: 'Synopsis',
                            ),
                            const SizedBox(height: 10),
                            AnimatedSize(
                              duration: const Duration(milliseconds: 300),
                              curve: Curves.easeOut,
                              child: Text(
                                m.description!,
                                style: theme.textTheme.bodySmall?.copyWith(
                                  height: 1.55,
                                  color: cs.onSurface.withValues(alpha: 0.8),
                                ),
                                maxLines:
                                    _descExpanded ? null : 4,
                                overflow: _descExpanded
                                    ? TextOverflow.visible
                                    : TextOverflow.ellipsis,
                              ),
                            ),
                            const SizedBox(height: 8),
                            GestureDetector(
                              onTap: () => setState(
                                  () => _descExpanded = !_descExpanded),
                              child: Text(
                                _descExpanded ? 'Show less' : 'Read more',
                                style: TextStyle(
                                  color: cs.primary,
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                if (m.description != null && m.description!.isNotEmpty)
                  const SliverToBoxAdapter(child: SizedBox(height: 16)),

                // ── Stats grid ─────────────────────────────────────────────
                SliverToBoxAdapter(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    child: detail.when(
                      loading: () => _StatsGrid(media: m, detail: null),
                      error: (_, __) => _StatsGrid(media: m, detail: null),
                      data: (d) => _StatsGrid(media: m, detail: d),
                    ),
                  ),
                ),

                const SliverToBoxAdapter(child: SizedBox(height: 16)),

                // ── Studios ────────────────────────────────────────────────
                if (detail.valueOrNull?.studios.isNotEmpty == true)
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      child: _GlassCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _SectionTitle(
                              icon: Icons.business_rounded,
                              label: 'Studios',
                            ),
                            const SizedBox(height: 10),
                            Wrap(
                              spacing: 8,
                              runSpacing: 8,
                              children: detail.valueOrNull!.studios
                                  .map((s) => _StudioPill(s))
                                  .toList(),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                if (detail.valueOrNull?.studios.isNotEmpty == true)
                  const SliverToBoxAdapter(child: SizedBox(height: 16)),

                // ── Tags ───────────────────────────────────────────────────
                if (detail.valueOrNull?.tags.isNotEmpty == true)
                  SliverToBoxAdapter(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      child: _GlassCard(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _SectionTitle(
                              icon: Icons.label_outline_rounded,
                              label: 'Tags',
                            ),
                            const SizedBox(height: 10),
                            Wrap(
                              spacing: 7,
                              runSpacing: 7,
                              children: detail.valueOrNull!.tags
                                  .map((t) => _TagPill(t))
                                  .toList(),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),

                if (detail.valueOrNull?.tags.isNotEmpty == true)
                  const SliverToBoxAdapter(child: SizedBox(height: 16)),

                // ── Characters ─────────────────────────────────────────────
                if (detail.valueOrNull?.characters.isNotEmpty == true)
                  _HorizontalSection(
                    title: 'Characters',
                    icon: Icons.people_outline_rounded,
                    height: 130,
                    itemCount: detail.valueOrNull!.characters.length,
                    itemBuilder: (i) {
                      final c = detail.valueOrNull!.characters[i];
                      return _CharacterCard(character: c);
                    },
                  ),

                if (detail.valueOrNull?.characters.isNotEmpty == true)
                  const SliverToBoxAdapter(child: SizedBox(height: 16)),

                // ── Relations ──────────────────────────────────────────────
                if (detail.valueOrNull?.relations.isNotEmpty == true)
                  _HorizontalSection(
                    title: 'Related',
                    icon: Icons.account_tree_outlined,
                    height: 180,
                    itemCount: detail.valueOrNull!.relations.length,
                    itemBuilder: (i) {
                      final r = detail.valueOrNull!.relations[i];
                      return _RelationCard(
                        relation: r,
                        onTap: () {
                          // open as AnilistMedia stub
                          context.push('/anilistDetail',
                              extra: AnilistMedia(
                                id: r.id,
                                type: r.type,
                                format: r.format,
                                titleRomaji: r.title,
                                coverLarge: r.coverImage,
                              ));
                        },
                      );
                    },
                  ),

                if (detail.valueOrNull?.relations.isNotEmpty == true)
                  const SliverToBoxAdapter(child: SizedBox(height: 16)),

                // ── Recommendations ────────────────────────────────────────
                if (detail.valueOrNull?.recommendations.isNotEmpty == true)
                  _HorizontalSection(
                    title: 'You Might Also Like',
                    icon: Icons.thumb_up_outlined,
                    height: 190,
                    itemCount: detail.valueOrNull!.recommendations.length,
                    itemBuilder: (i) {
                      final r = detail.valueOrNull!.recommendations[i];
                      return _RecommendCard(
                        media: r,
                        onTap: () =>
                            context.push('/anilistDetail', extra: r),
                      );
                    },
                  ),

                if (detail.valueOrNull?.recommendations.isNotEmpty == true)
                  const SliverToBoxAdapter(child: SizedBox(height: 16)),

                // ── Loading indicator for detail ───────────────────────────
                if (detail.isLoading)
                  const SliverToBoxAdapter(
                    child: Padding(
                      padding: EdgeInsets.symmetric(vertical: 20),
                      child: Center(
                        child: SizedBox(
                          width: 24,
                          height: 24,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        ),
                      ),
                    ),
                  ),

                const SliverToBoxAdapter(child: SizedBox(height: 100)),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Stats grid widget
// ─────────────────────────────────────────────────────────────────────────────

class _StatsGrid extends StatelessWidget {
  final AnilistMedia media;
  final AnilistMediaDetail? detail;

  const _StatsGrid({required this.media, required this.detail});

  String _fmt(String? s) {
    if (s == null || s.isEmpty) return '—';
    return s;
  }

  String _fmtStatus(String? s) => switch (s) {
        'FINISHED' => 'Finished',
        'RELEASING' => 'Releasing',
        'NOT_YET_RELEASED' => 'Coming Soon',
        'CANCELLED' => 'Cancelled',
        'HIATUS' => 'On Hiatus',
        _ => s ?? '—',
      };

  String _fmtSeason(String? season, int? year) {
    final parts = <String>[];
    if (season != null) {
      parts.add(
          '${season[0]}${season.substring(1).toLowerCase()}');
    }
    if (year != null) parts.add(year.toString());
    return parts.isEmpty ? '—' : parts.join(' ');
  }

  String _fmtSource(String? s) {
    if (s == null) return '—';
    return s.replaceAll('_', ' ').split(' ').map((w) {
      if (w.isEmpty) return w;
      return '${w[0].toUpperCase()}${w.substring(1).toLowerCase()}';
    }).join(' ');
  }

  @override
  Widget build(BuildContext context) {
    final m = media;
    final d = detail;

    final episodesOrChapters = m.type == 'MANGA'
        ? (m.chapters != null ? '${m.chapters}' : '—')
        : (m.episodes != null ? '${m.episodes}' : '—');
    final epLabel = m.type == 'MANGA' ? 'Chapters' : 'Episodes';

    final stats = [
      _Stat(
        icon: Icons.category_outlined,
        label: 'Format',
        value: _fmt(m.format?.replaceAll('_', ' ')),
      ),
      _Stat(
        icon: Icons.star_rounded,
        label: 'Score',
        value: m.averageScore != null
            ? '${(m.averageScore! / 10).toStringAsFixed(1)}/10'
            : '—',
      ),
      _Stat(
        icon: Icons.live_tv_outlined,
        label: epLabel,
        value: episodesOrChapters,
      ),
      _Stat(
        icon: Icons.info_outline_rounded,
        label: 'Status',
        value: _fmtStatus(d?.status),
      ),
      _Stat(
        icon: Icons.calendar_month_outlined,
        label: 'Season',
        value: _fmtSeason(d?.season, d?.seasonYear ?? d?.startYear),
      ),
      _Stat(
        icon: Icons.public_outlined,
        label: 'Country',
        value: switch (m.countryOfOrigin) {
          'JP' => '🇯🇵 Japan',
          'KR' => '🇰🇷 Korea',
          'CN' => '🇨🇳 China',
          'TW' => '🇹🇼 Taiwan',
          _ => m.countryOfOrigin ?? '—',
        },
      ),
      if (d?.duration != null)
        _Stat(
          icon: Icons.timer_outlined,
          label: 'Duration',
          value: '${d!.duration} min',
        ),
      if (d?.source != null)
        _Stat(
          icon: Icons.menu_book_outlined,
          label: 'Source',
          value: _fmtSource(d!.source),
        ),
    ];

    return _GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _SectionTitle(icon: Icons.bar_chart_rounded, label: 'Information'),
          const SizedBox(height: 12),
          GridView.builder(
            physics: const NeverScrollableScrollPhysics(),
            shrinkWrap: true,
            gridDelegate:
                const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              childAspectRatio: 2.8,
              crossAxisSpacing: 10,
              mainAxisSpacing: 10,
            ),
            itemCount: stats.length,
            itemBuilder: (_, i) => _StatTile(stats[i]),
          ),
        ],
      ),
    );
  }
}

class _Stat {
  final IconData icon;
  final String label;
  final String value;
  const _Stat({required this.icon, required this.label, required this.value});
}

class _StatTile extends StatelessWidget {
  final _Stat stat;
  const _StatTile(this.stat);

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: cs.surfaceContainerHighest.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          Icon(stat.icon, size: 15, color: cs.primary),
          const SizedBox(width: 6),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  stat.label,
                  style: TextStyle(
                    fontSize: 10,
                    color: cs.onSurface.withValues(alpha: 0.5),
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  stat.value,
                  style: TextStyle(
                    fontSize: 12,
                    color: cs.onSurface,
                    fontWeight: FontWeight.w700,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Horizontal section (characters, relations, recommendations)
// ─────────────────────────────────────────────────────────────────────────────

class _HorizontalSection extends StatelessWidget {
  final String title;
  final IconData icon;
  final double height;
  final int itemCount;
  final Widget Function(int) itemBuilder;

  const _HorizontalSection({
    required this.title,
    required this.icon,
    required this.height,
    required this.itemCount,
    required this.itemBuilder,
  });

  @override
  Widget build(BuildContext context) {
    return SliverToBoxAdapter(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: _SectionTitle(icon: icon, label: title),
          ),
          const SizedBox(height: 10),
          SizedBox(
            height: height,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 20),
              itemCount: itemCount,
              separatorBuilder: (_, __) => const SizedBox(width: 10),
              itemBuilder: (_, i) => itemBuilder(i),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Character card
// ─────────────────────────────────────────────────────────────────────────────

class _CharacterCard extends StatelessWidget {
  final AnilistCharacter character;
  const _CharacterCard({required this.character});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return SizedBox(
      width: 78,
      child: Column(
        children: [
          ClipRRect(
            borderRadius: BorderRadius.circular(40),
            child: Container(
              width: 70,
              height: 70,
              color: cs.surfaceContainerHighest,
              child: character.imageUrl != null
                  ? ExtendedImage.network(
                      character.imageUrl!,
                      fit: BoxFit.cover,
                      cache: true,
                    )
                  : const Icon(Icons.person_rounded, size: 32),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            character.name,
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 10.5,
              fontWeight: FontWeight.w600,
              color: cs.onSurface,
            ),
          ),
          if (character.role != null)
            Text(
              character.role!,
              textAlign: TextAlign.center,
              maxLines: 1,
              style: TextStyle(
                fontSize: 9.5,
                color: cs.onSurface.withValues(alpha: 0.50),
              ),
            ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Relation card
// ─────────────────────────────────────────────────────────────────────────────

class _RelationCard extends StatelessWidget {
  final AnilistRelation relation;
  final VoidCallback onTap;
  const _RelationCard({required this.relation, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return GestureDetector(
      onTap: onTap,
      child: SizedBox(
        width: 100,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: SizedBox(
                width: 100,
                height: 138,
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    relation.coverImage != null
                        ? ExtendedImage.network(
                            relation.coverImage!,
                            fit: BoxFit.cover,
                            cache: true,
                          )
                        : Container(color: cs.surfaceContainerHighest),
                    if (relation.relationType != null)
                      Positioned(
                        bottom: 0,
                        left: 0,
                        right: 0,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 4),
                          color: Colors.black.withValues(alpha: 0.65),
                          child: Text(
                            _friendlyRelationType(relation.relationType),
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 9.5,
                              fontWeight: FontWeight.w700,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 5),
            Text(
              relation.title,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: cs.onSurface,
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _friendlyRelationType(String? r) => switch (r) {
        'SEQUEL' => 'Sequel',
        'PREQUEL' => 'Prequel',
        'PARENT' => 'Parent',
        'SIDE_STORY' => 'Side Story',
        'SPIN_OFF' => 'Spin-off',
        'ADAPTATION' => 'Adaptation',
        'ALTERNATIVE' => 'Alternative',
        'SOURCE' => 'Source',
        'COMPILATION' => 'Compilation',
        'CHARACTER' => 'Character',
        'SUMMARY' => 'Summary',
        'CONTAINS' => 'Contains',
        'OTHER' => 'Other',
        _ => r ?? '',
      };
}

// ─────────────────────────────────────────────────────────────────────────────
// Recommendation card
// ─────────────────────────────────────────────────────────────────────────────

class _RecommendCard extends StatelessWidget {
  final AnilistMedia media;
  final VoidCallback onTap;
  const _RecommendCard({required this.media, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return GestureDetector(
      onTap: onTap,
      child: SizedBox(
        width: 100,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(12),
              child: SizedBox(
                width: 100,
                height: 145,
                child: media.bestCover != null
                    ? ExtendedImage.network(
                        media.bestCover!,
                        fit: BoxFit.cover,
                        cache: true,
                      )
                    : Container(color: cs.surfaceContainerHighest),
              ),
            ),
            const SizedBox(height: 5),
            Text(
              media.displayTitle,
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w600,
                color: cs.onSurface,
              ),
            ),
            if (media.averageScore != null)
              Row(
                children: [
                  const Icon(Icons.star_rounded,
                      size: 11, color: Colors.amber),
                  const SizedBox(width: 2),
                  Text(
                    (media.averageScore! / 10).toStringAsFixed(1),
                    style: TextStyle(
                      fontSize: 10,
                      color: cs.onSurface.withValues(alpha: 0.6),
                    ),
                  ),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared helpers / primitives
// ─────────────────────────────────────────────────────────────────────────────

class _GlassCard extends StatelessWidget {
  final Widget child;
  const _GlassCard({required this.child});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: cs.surfaceContainerLow.withValues(alpha: 0.85),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
            color: cs.outlineVariant.withValues(alpha: 0.3), width: 1),
      ),
      child: child,
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final IconData icon;
  final String label;
  const _SectionTitle({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Row(
      children: [
        Icon(icon, size: 17, color: cs.primary),
        const SizedBox(width: 7),
        Text(
          label,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w700,
            color: cs.onSurface,
          ),
        ),
      ],
    );
  }
}

class _CircleBtn extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  const _CircleBtn({required this.icon, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: 42,
        height: 42,
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          color: cs.surfaceContainerLow.withValues(alpha: 0.8),
          border: Border.all(
              color: cs.outlineVariant.withValues(alpha: 0.3)),
        ),
        child: Icon(icon, color: cs.onSurface, size: 20),
      ),
    );
  }
}

class _ActionBtn extends StatelessWidget {
  final IconData icon;
  final String? label;
  final bool primary;
  final double? width;
  final VoidCallback onTap;

  const _ActionBtn({
    required this.icon,
    required this.onTap,
    this.label,
    this.primary = false,
    this.width,
  });

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return GestureDetector(
      onTap: onTap,
      child: Container(
        width: width,
        height: 50,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        decoration: BoxDecoration(
          color: primary
              ? cs.primary
              : cs.surfaceContainerHighest.withValues(alpha: 0.85),
          borderRadius: BorderRadius.circular(14),
          border: primary
              ? null
              : Border.all(color: cs.outlineVariant.withValues(alpha: 0.4)),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon,
                color: primary ? cs.onPrimary : cs.onSurface, size: 20),
            if (label != null) ...[
              const SizedBox(width: 8),
              Flexible(
                child: Text(
                  label!,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    color: primary ? cs.onPrimary : cs.onSurface,
                    fontWeight: FontWeight.w700,
                    fontSize: 14,
                  ),
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _TypeBadge extends StatelessWidget {
  final String type;
  final String? format;
  final String? country;
  const _TypeBadge(this.type, this.format, this.country);

  String get _label {
    if (format == 'NOVEL') return 'Novel';
    if (country == 'KR') return 'Manhwa';
    if (country == 'CN') return 'Manhua';
    return type == 'MANGA' ? 'Manga' : 'Anime';
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: cs.primaryContainer,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        _label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w700,
          color: cs.onPrimaryContainer,
          letterSpacing: 0.5,
        ),
      ),
    );
  }
}

class _ScorePill extends StatelessWidget {
  final int score;
  const _ScorePill(this.score);

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(
        color: Colors.amber.withValues(alpha: 0.18),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: Colors.amber.withValues(alpha: 0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          const Icon(Icons.star_rounded, size: 13, color: Colors.amber),
          const SizedBox(width: 3),
          Text(
            (score / 10).toStringAsFixed(1),
            style: const TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w700,
              color: Colors.amber,
            ),
          ),
        ],
      ),
    );
  }
}

class _GenreChip extends StatelessWidget {
  final String genre;
  const _GenreChip(this.genre);

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: cs.secondaryContainer.withValues(alpha: 0.6),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: cs.secondary.withValues(alpha: 0.25)),
      ),
      child: Text(
        genre,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          color: cs.onSecondaryContainer,
        ),
      ),
    );
  }
}

class _StudioPill extends StatelessWidget {
  final String name;
  const _StudioPill(this.name);

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: cs.tertiaryContainer.withValues(alpha: 0.5),
        borderRadius: BorderRadius.circular(10),
        border:
            Border.all(color: cs.tertiary.withValues(alpha: 0.3)),
      ),
      child: Text(
        name,
        style: TextStyle(
          fontSize: 12.5,
          fontWeight: FontWeight.w600,
          color: cs.onTertiaryContainer,
        ),
      ),
    );
  }
}

class _TagPill extends StatelessWidget {
  final String tag;
  const _TagPill(this.tag);

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(
        color: cs.surfaceContainerHighest.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        tag,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w500,
          color: cs.onSurface.withValues(alpha: 0.75),
        ),
      ),
    );
  }
}
