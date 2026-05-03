import 'package:isar_community/isar.dart';
import 'package:watchtower/eval/model/m_manga.dart';
import 'package:watchtower/eval/model/m_pages.dart';
import 'package:watchtower/main.dart';
import 'package:watchtower/models/manga.dart';
import 'package:watchtower/models/source.dart';
import 'package:watchtower/services/isolate_service.dart';
import 'package:watchtower/utils/log/logger.dart';

enum DiagStep { popular, latest, detail, media }

class DiagStepResult {
  final bool ok;
  final String? error;
  final int? count;
  final int ms;
  const DiagStepResult({
    required this.ok,
    this.error,
    this.count,
    required this.ms,
  });
}

class ExtDiagResult {
  final Source source;
  final Map<DiagStep, DiagStepResult> steps;
  bool get allOk => steps.values.every((s) => s.ok);
  bool get anyFailed => steps.values.any((s) => !s.ok);

  const ExtDiagResult({required this.source, required this.steps});
}

typedef OnExtResult = void Function(ExtDiagResult result);

Future<List<ExtDiagResult>> runExtensionDiagnosticsFull(
  ItemType itemType, {
  OnExtResult? onResult,
}) async {
  final sources = isar.sources
      .filter()
      .idIsNotNull()
      .and()
      .isAddedEqualTo(true)
      .and()
      .itemTypeEqualTo(itemType)
      .findAllSync()
      .where((s) => !(s.name == 'local' && (s.lang?.isEmpty ?? true)))
      .toList();

  AppLogger.log(
    '🔬 Diagnostics démarrés — type=${itemType.name} | sources=${sources.length}',
    logLevel: LogLevel.info,
    tag: kLogTagExt,
  );

  final results = <ExtDiagResult>[];
  final futures = sources.map((src) async {
    final result = await _diagnoseSource(src, itemType);
    results.add(result);
    onResult?.call(result);
    final status = result.allOk ? '✅' : '❌';
    AppLogger.log(
      '$status ${src.name} [${src.lang}] — '
      '${result.steps.entries.map((e) => '${e.key.name}:${e.value.ok ? "OK" : "FAIL"}').join(" ")}',
      logLevel: result.anyFailed ? LogLevel.warning : LogLevel.info,
      tag: kLogTagExt,
    );
    return result;
  }).toList();

  await Future.wait(futures);

  final ok = results.where((r) => r.allOk).length;
  final failed = results.length - ok;
  AppLogger.log(
    '🔬 Diagnostics terminés — ok=$ok | failed=$failed | total=${results.length}',
    logLevel: failed > 0 ? LogLevel.warning : LogLevel.info,
    tag: kLogTagExt,
  );

  return results;
}

Future<ExtDiagResult> _diagnoseSource(Source src, ItemType itemType) async {
  final steps = <DiagStep, DiagStepResult>{};

  // ── Step 1 : getPopular ────────────────────────────────────────────────────
  String? firstItemUrl;
  {
    final sw = Stopwatch()..start();
    try {
      final pages = await getIsolateService
          .get<MPages>(
            page: 1,
            source: src,
            serviceType: 'getPopular',
          )
          .timeout(const Duration(seconds: 45));
      sw.stop();
      final count = pages.list?.length ?? 0;
      firstItemUrl = count > 0 ? pages.list!.first.link : null;
      steps[DiagStep.popular] = DiagStepResult(
        ok: count > 0,
        count: count,
        ms: sw.elapsedMilliseconds,
        error: count == 0 ? 'Aucun résultat' : null,
      );
    } catch (e) {
      sw.stop();
      steps[DiagStep.popular] = DiagStepResult(
        ok: false,
        error: e.toString().split('\n').first,
        ms: sw.elapsedMilliseconds,
      );
    }
  }

  // ── Step 2 : getLatestUpdates ──────────────────────────────────────────────
  {
    final sw = Stopwatch()..start();
    try {
      final pages = await getIsolateService
          .get<MPages>(
            page: 1,
            source: src,
            serviceType: 'getLatestUpdates',
          )
          .timeout(const Duration(seconds: 45));
      sw.stop();
      final count = pages.list?.length ?? 0;
      steps[DiagStep.latest] = DiagStepResult(
        ok: count > 0,
        count: count,
        ms: sw.elapsedMilliseconds,
        error: count == 0 ? 'Aucun résultat' : null,
      );
    } catch (e) {
      sw.stop();
      steps[DiagStep.latest] = DiagStepResult(
        ok: false,
        error: e.toString().split('\n').first,
        ms: sw.elapsedMilliseconds,
      );
    }
  }

  // ── Step 3 : getDetail ─────────────────────────────────────────────────────
  String? firstEpisodeUrl;
  if (firstItemUrl != null) {
    final sw = Stopwatch()..start();
    try {
      final detail = await getIsolateService
          .get<MManga>(
            url: firstItemUrl,
            source: src,
            serviceType: 'getDetail',
          )
          .timeout(const Duration(seconds: 45));
      sw.stop();
      final chapCount = detail.chapters?.length ?? 0;
      firstEpisodeUrl = chapCount > 0 ? detail.chapters!.first.url : null;
      steps[DiagStep.detail] = DiagStepResult(
        ok: detail.name != null && detail.name!.isNotEmpty,
        count: chapCount,
        ms: sw.elapsedMilliseconds,
        error: (detail.name == null || detail.name!.isEmpty)
            ? 'Détail vide'
            : null,
      );
    } catch (e) {
      sw.stop();
      steps[DiagStep.detail] = DiagStepResult(
        ok: false,
        error: e.toString().split('\n').first,
        ms: sw.elapsedMilliseconds,
      );
    }
  } else {
    steps[DiagStep.detail] = const DiagStepResult(
      ok: false,
      error: 'Ignoré (pas d\'URL)',
      ms: 0,
    );
  }

  // ── Step 4 : getVideoList / getPageList ───────────────────────────────────
  if (firstEpisodeUrl != null) {
    final sw = Stopwatch()..start();
    final svcType =
        itemType == ItemType.anime ? 'getVideoList' : 'getPageList';
    try {
      final list = await getIsolateService
          .get<List<dynamic>>(
            url: firstEpisodeUrl,
            source: src,
            serviceType: svcType,
          )
          .timeout(const Duration(seconds: 45));
      sw.stop();
      final count = list.length;
      steps[DiagStep.media] = DiagStepResult(
        ok: count > 0,
        count: count,
        ms: sw.elapsedMilliseconds,
        error: count == 0 ? 'Aucun média' : null,
      );
    } catch (e) {
      sw.stop();
      steps[DiagStep.media] = DiagStepResult(
        ok: false,
        error: e.toString().split('\n').first,
        ms: sw.elapsedMilliseconds,
      );
    }
  } else {
    steps[DiagStep.media] = const DiagStepResult(
      ok: false,
      error: 'Ignoré (pas d\'URL épisode)',
      ms: 0,
    );
  }

  return ExtDiagResult(source: src, steps: steps);
}
