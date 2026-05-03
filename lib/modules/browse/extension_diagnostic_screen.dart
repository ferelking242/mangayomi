import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:isar_community/isar.dart';
import 'package:watchtower/main.dart';
import 'package:watchtower/models/manga.dart';
import 'package:watchtower/models/source.dart';
import 'package:watchtower/services/extension_diagnostics.dart';
import 'package:watchtower/utils/language.dart';

class ExtensionDiagnosticScreen extends StatefulWidget {
  final ItemType itemType;
  const ExtensionDiagnosticScreen({required this.itemType, super.key});

  @override
  State<ExtensionDiagnosticScreen> createState() =>
      _ExtensionDiagnosticScreenState();
}

class _ExtensionDiagnosticScreenState extends State<ExtensionDiagnosticScreen> {
  List<ExtDiagResult> _results = [];
  bool _running = false;
  bool _done = false;
  int _total = 0;

  @override
  void initState() {
    super.initState();
    _total = _countSources();
    _startDiagnostics();
  }

  int _countSources() {
    return isar.sources
        .filter()
        .idIsNotNull()
        .and()
        .isAddedEqualTo(true)
        .and()
        .itemTypeEqualTo(widget.itemType)
        .findAllSync()
        .where((s) => !(s.name == 'local' && s.lang == ''))
        .length;
  }

  Future<void> _startDiagnostics() async {
    if (_running) return;
    setState(() {
      _running = true;
      _done = false;
      _results = [];
    });
    await runExtensionDiagnosticsFull(
      widget.itemType,
      onResult: (result) {
        if (mounted) setState(() => _results.add(result));
      },
    );
    if (mounted) setState(() {
      _running = false;
      _done = true;
    });
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final ok = _results.where((r) => r.allOk).length;
    final failed = _results.where((r) => r.anyFailed).length;

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () => context.pop(),
        ),
        title: const Text('Diagnostic des extensions'),
        actions: [
          if (!_running)
            IconButton(
              tooltip: 'Relancer',
              icon: const Icon(Icons.refresh_rounded),
              onPressed: _startDiagnostics,
            ),
        ],
      ),
      body: Column(
        children: [
          // ── Summary bar ─────────────────────────────────────────────────
          _SummaryBar(
            total: _total,
            done: _results.length,
            ok: ok,
            failed: failed,
            running: _running,
            done_: _done,
          ),
          // ── Results list ────────────────────────────────────────────────
          Expanded(
            child: _results.isEmpty && _running
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 8,
                    ),
                    itemCount: _results.length,
                    itemBuilder: (_, i) =>
                        _ExtDiagCard(result: _results[i], cs: cs),
                  ),
          ),
        ],
      ),
    );
  }
}

// ─── Summary Bar ─────────────────────────────────────────────────────────────

class _SummaryBar extends StatelessWidget {
  final int total;
  final int done;
  final int ok;
  final int failed;
  final bool running;
  final bool done_;

  const _SummaryBar({
    required this.total,
    required this.done,
    required this.ok,
    required this.failed,
    required this.running,
    required this.done_,
  });

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final progress = total == 0 ? 0.0 : done / total;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
      decoration: BoxDecoration(
        color: cs.surfaceContainerHigh,
        border: Border(bottom: BorderSide(color: cs.outlineVariant, width: 1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              if (running) ...[
                SizedBox(
                  width: 14,
                  height: 14,
                  child: CircularProgressIndicator(
                    strokeWidth: 2,
                    color: cs.primary,
                  ),
                ),
                const SizedBox(width: 8),
              ],
              Text(
                running
                    ? 'Test en cours… $done/$total'
                    : done_
                    ? '✅ Terminé · $ok OK · $failed échec(s)'
                    : 'En attente…',
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  color: done_ && failed > 0 ? cs.error : cs.onSurface,
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: progress,
              minHeight: 4,
              backgroundColor: cs.surfaceContainerHighest,
              valueColor: AlwaysStoppedAnimation(
                failed > 0 ? cs.error : cs.primary,
              ),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '4 étapes par extension : Popular · Latest · Détail · Médias',
            style: TextStyle(fontSize: 10.5, color: cs.onSurfaceVariant),
          ),
        ],
      ),
    );
  }
}

// ─── Per-extension card ───────────────────────────────────────────────────────

class _ExtDiagCard extends StatelessWidget {
  final ExtDiagResult result;
  final ColorScheme cs;

  const _ExtDiagCard({required this.result, required this.cs});

  @override
  Widget build(BuildContext context) {
    final src = result.source;
    final allOk = result.allOk;

    return Card(
      margin: const EdgeInsets.symmetric(vertical: 4),
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: allOk
              ? Colors.green.withOpacity(0.35)
              : cs.error.withOpacity(0.4),
          width: 1,
        ),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // ── Header ──────────────────────────────────────────────────
            Row(
              children: [
                Icon(
                  allOk ? Icons.check_circle_rounded : Icons.error_rounded,
                  color: allOk ? Colors.green : cs.error,
                  size: 18,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    src.name ?? 'Unknown',
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 13.5,
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 7,
                    vertical: 2,
                  ),
                  decoration: BoxDecoration(
                    color: cs.surfaceContainerHighest,
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: Text(
                    completeLanguageName(src.lang ?? '').toUpperCase(),
                    style: TextStyle(
                      fontSize: 9,
                      fontWeight: FontWeight.w800,
                      color: cs.onSurfaceVariant,
                      letterSpacing: 0.5,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            // ── Step chips ───────────────────────────────────────────────
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: DiagStep.values.map((step) {
                final sr = result.steps[step];
                return _StepChip(step: step, result: sr, cs: cs);
              }).toList(),
            ),
            // ── Errors ───────────────────────────────────────────────────
            ...result.steps.entries
                .where((e) => !e.value.ok && e.value.error != null)
                .map((e) => Padding(
                      padding: const EdgeInsets.only(top: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(
                            Icons.warning_amber_rounded,
                            size: 13,
                            color: cs.error.withOpacity(0.8),
                          ),
                          const SizedBox(width: 4),
                          Expanded(
                            child: Text(
                              '[${_stepLabel(e.key)}] ${e.value.error}',
                              style: TextStyle(
                                fontSize: 10.5,
                                color: cs.onSurfaceVariant,
                                fontFamily: 'monospace',
                              ),
                            ),
                          ),
                        ],
                      ),
                    )),
          ],
        ),
      ),
    );
  }

  String _stepLabel(DiagStep step) {
    switch (step) {
      case DiagStep.popular:
        return 'Popular';
      case DiagStep.latest:
        return 'Latest';
      case DiagStep.detail:
        return 'Détail';
      case DiagStep.media:
        return 'Médias';
    }
  }
}

class _StepChip extends StatelessWidget {
  final DiagStep step;
  final DiagStepResult? result;
  final ColorScheme cs;

  const _StepChip({
    required this.step,
    required this.result,
    required this.cs,
  });

  @override
  Widget build(BuildContext context) {
    if (result == null) {
      return _chip('…', cs.surfaceContainerHighest, cs.onSurfaceVariant);
    }
    final ok = result!.ok;
    final label = _buildLabel();
    final bg = ok
        ? Colors.green.withOpacity(0.12)
        : cs.errorContainer.withOpacity(0.5);
    final fg = ok ? Colors.green.shade700 : cs.onErrorContainer;

    return _chip(label, bg, fg);
  }

  String _buildLabel() {
    final prefix = switch (step) {
      DiagStep.popular => '📋',
      DiagStep.latest => '🕐',
      DiagStep.detail => '🔍',
      DiagStep.media => '▶️',
    };
    final name = switch (step) {
      DiagStep.popular => 'Popular',
      DiagStep.latest => 'Latest',
      DiagStep.detail => 'Détail',
      DiagStep.media => 'Médias',
    };
    final status = result!.ok ? '✓' : '✗';
    final count = result!.count != null ? ' ${result!.count}' : '';
    final ms = '${result!.ms}ms';
    return '$prefix $name $status$count · $ms';
  }

  Widget _chip(String label, Color bg, Color fg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 11, color: fg, fontWeight: FontWeight.w600),
      ),
    );
  }
}
