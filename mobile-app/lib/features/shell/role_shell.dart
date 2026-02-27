import 'dart:math' as math;
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;

import '../../app/theme.dart';
import '../../core/i18n.dart';
import '../../core/models.dart';
import '../common/widgets.dart';
import '../consumer/product_journey_screen.dart';

class RoleShell extends StatefulWidget {
  const RoleShell({
    super.key,
    required this.session,
    required this.onLogout,
    required this.onThemeModeChanged,
    required this.themeMode,
    required this.i18n,
  });

  final AuthSession session;
  final VoidCallback onLogout;
  final ValueChanged<ThemeMode> onThemeModeChanged;
  final ThemeMode themeMode;
  final I18nController i18n;

  @override
  State<RoleShell> createState() => _RoleShellState();
}

class _RoleShellState extends State<RoleShell> {
  static const String _backendBaseUrl = String.fromEnvironment(
    'BACKEND_OTP_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000/api/v1',
  );
  static const String _backendBaseUrls = String.fromEnvironment(
    'BACKEND_OTP_BASE_URLS',
    defaultValue:
        'http://127.0.0.1:8000/api/v1,http://10.0.2.2:8000/api/v1,http://localhost:8000/api/v1',
  );
  static const String _aiBaseUrl = String.fromEnvironment(
    'AI_SERVICE_BASE_URL',
    defaultValue: 'http://127.0.0.1:8001',
  );
  static const String _aiBaseUrls = String.fromEnvironment(
    'AI_SERVICE_BASE_URLS',
    defaultValue:
        'http://127.0.0.1:8001,http://10.0.2.2:8001,http://localhost:8001',
  );

  int _index = 0;
  DashboardPayload? _dashboard;
  bool _dashboardLoading = false;
  String? _dashboardError;

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    if (_dashboardLoading) {
      return;
    }
    setState(() {
      _dashboardLoading = true;
      _dashboardError = null;
    });

    for (final baseUrl in _backendBaseUrlCandidates()) {
      try {
        final response = await http
            .get(
              Uri.parse(_apiUrl(baseUrl, '/auth/mobile-dashboard')),
              headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ${widget.session.accessToken}',
              },
            )
            .timeout(const Duration(seconds: 12));

        if (response.statusCode >= 200 && response.statusCode < 300) {
          final body = jsonDecode(response.body) as Map<String, dynamic>;
          if (!mounted) {
            return;
          }
          setState(() {
            _dashboard = DashboardPayload.fromJson(body);
            _dashboardLoading = false;
            _dashboardError = null;
          });
          return;
        }
      } catch (_) {
        continue;
      }
    }

    if (!mounted) {
      return;
    }
    setState(() {
      _dashboardLoading = false;
      _dashboardError = 'Unable to fetch live dashboard data from backend.';
    });
  }

  List<String> _backendBaseUrlCandidates() {
    final seen = <String>{};
    final candidates = <String>[];

    void addCandidate(String value) {
      final trimmed = value.trim();
      if (trimmed.isEmpty || seen.contains(trimmed)) {
        return;
      }
      seen.add(trimmed);
      candidates.add(trimmed);
    }

    addCandidate(_backendBaseUrl);
    for (final item in _backendBaseUrls.split(',')) {
      addCandidate(item);
    }
    return candidates;
  }

  String _apiUrl(String baseUrl, String path) {
    final normalizedBase = baseUrl.endsWith('/')
        ? baseUrl.substring(0, baseUrl.length - 1)
        : baseUrl;
    final normalizedPath = path.startsWith('/') ? path : '/$path';
    if (normalizedBase.endsWith('/api/v1')) {
      return '$normalizedBase$normalizedPath';
    }
    return '$normalizedBase/api/v1$normalizedPath';
  }

  List<String> _aiBaseUrlCandidates() {
    final seen = <String>{};
    final candidates = <String>[];

    void addCandidate(String value) {
      final trimmed = value.trim();
      if (trimmed.isEmpty || seen.contains(trimmed)) {
        return;
      }
      seen.add(trimmed);
      candidates.add(trimmed);
    }

    addCandidate(_aiBaseUrl);
    for (final item in _aiBaseUrls.split(',')) {
      addCandidate(item);
    }
    return candidates;
  }

  String _aiUrl(String baseUrl) {
    final normalizedBase = baseUrl.endsWith('/')
        ? baseUrl.substring(0, baseUrl.length - 1)
        : baseUrl;
    if (normalizedBase.endsWith('/chat')) {
      return normalizedBase;
    }
    return '$normalizedBase/chat';
  }

  String _roleApiValue(AppRole role) {
    switch (role) {
      case AppRole.farmer:
        return 'farmer';
      case AppRole.distributor:
        return 'distributor';
      case AppRole.retailer:
        return 'retailer';
      case AppRole.consumer:
        return 'consumer';
    }
  }

  Future<String> _askAiService(String message) async {
    for (final baseUrl in _aiBaseUrlCandidates()) {
      try {
        final response = await http
            .post(
              Uri.parse(_aiUrl(baseUrl)),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({
                'role': _roleApiValue(widget.session.role),
                'message': message,
                'session_id': widget.session.userId,
                'language': widget.i18n.lang,
              }),
            )
            .timeout(const Duration(seconds: 20));

        if (response.statusCode >= 200 && response.statusCode < 300) {
          final body = jsonDecode(response.body) as Map<String, dynamic>;
          final reply = body['response']?.toString().trim();
          if (reply != null && reply.isNotEmpty) {
            return reply;
          }
        }
      } catch (_) {
        continue;
      }
    }

    return 'AI service is unreachable. Start ai-service and use adb reverse tcp:8001 tcp:8001 for USB device.';
  }

  void _openAiAssistant() {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        fullscreenDialog: true,
        builder: (_) => _AiAssistantPage(
          onSend: _askAiService,
          roleTitle: widget.session.role.title,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tabs = _tabs();
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Scaffold(
      backgroundColor: Theme.of(context).scaffoldBackgroundColor,
      body: SafeArea(
        child: Column(
          children: [
            _header(tabs[_index].label),
            _offlineBanner(),
            const SizedBox(height: 12),
            Expanded(
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: isDark
                      ? AppPalette.darkSurface
                      : AppPalette.lightSurface,
                  borderRadius: BorderRadius.circular(18),
                  border: Border.all(
                    color: isDark
                        ? AppPalette.darkBorder
                        : AppPalette.lightBorder,
                  ),
                ),
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 220),
                  child: KeyedSubtree(
                    key: ValueKey(_index),
                    child: tabs[_index].page,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        backgroundColor: Theme.of(context).colorScheme.secondary,
        foregroundColor: Theme.of(context).colorScheme.onSecondary,
        onPressed: _openAiAssistant,
        icon: const Icon(Icons.auto_awesome_rounded),
        label: const Text('AI'),
      ),
      bottomNavigationBar: NavigationBar(
        height: 76,
        selectedIndex: _index,
        onDestinationSelected: (index) => setState(() => _index = index),
        destinations: [
          for (final tab in tabs)
            NavigationDestination(icon: Icon(tab.icon), label: tab.label),
        ],
      ),
    );
  }

  Widget _header(String title) {
    return Container(
      margin: const EdgeInsets.fromLTRB(12, 10, 12, 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppPalette.brandGreenDark, AppPalette.brandGreen],
        ),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        children: [
          Container(
            width: 38,
            height: 38,
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(
              widget.session.role.icon,
              color: AppPalette.brandGreenDark,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              title,
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(color: Colors.white),
            ),
          ),
          IconButton(
            onPressed: _loadDashboard,
            icon: Icon(
              _dashboardLoading ? Icons.sync_rounded : Icons.refresh_rounded,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }

  Widget _offlineBanner() {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: isDark ? AppPalette.darkSurfaceAlt : AppPalette.lightSurfaceAlt,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isDark ? AppPalette.darkBorder : AppPalette.lightBorder,
        ),
      ),
      child: Row(
        children: [
          const Icon(Icons.cloud_off_rounded, size: 18),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              _dashboardError ??
                  (_dashboardLoading
                      ? 'Syncing live backend dashboard...'
                      : 'Live backend mode active'),
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          Icon(
            Icons.circle,
            size: 9,
            color: _dashboardError == null
                ? AppPalette.brandGreen
                : AppPalette.warningAmber,
          ),
        ],
      ),
    );
  }

  List<_TabConfig> _tabs() {
    switch (widget.session.role) {
      case AppRole.farmer:
        return [
          _TabConfig(
            widget.i18n.t('dashboard'),
            Icons.dashboard_rounded,
            _farmerDashboard(),
          ),
          _TabConfig('My Batches', Icons.inventory_2_rounded, _myBatches()),
          _TabConfig(
            widget.i18n.t('insights'),
            Icons.insights_rounded,
            _aiInsights(),
          ),
          _TabConfig(
            widget.i18n.t('profile'),
            Icons.person_rounded,
            _profile(),
          ),
        ];
      case AppRole.distributor:
        return [
          _TabConfig(
            widget.i18n.t('dashboard'),
            Icons.dashboard_rounded,
            _distributorDashboard(),
          ),
          _TabConfig(
            'Active Shipments',
            Icons.local_shipping_rounded,
            _activeShipments(),
          ),
          _TabConfig('Storage', Icons.warehouse_rounded, _storage()),
          _TabConfig(
            widget.i18n.t('profile'),
            Icons.person_rounded,
            _profile(),
          ),
        ];
      case AppRole.retailer:
        return [
          _TabConfig('Inventory', Icons.grid_view_rounded, _inventory()),
          _TabConfig('Incoming Batches', Icons.move_down_rounded, _incoming()),
          _TabConfig(
            widget.i18n.t('insights'),
            Icons.insights_rounded,
            _aiInsights(),
          ),
          _TabConfig(
            widget.i18n.t('profile'),
            Icons.person_rounded,
            _profile(),
          ),
        ];
      case AppRole.consumer:
        return [
          _TabConfig(
            widget.i18n.t('scan'),
            Icons.qr_code_scanner_rounded,
            _scanScreen(),
          ),
          _TabConfig(
            widget.i18n.t('explore'),
            Icons.travel_explore_rounded,
            _explore(),
          ),
          _TabConfig(
            widget.i18n.t('my_orders'),
            Icons.receipt_long_rounded,
            _orders(),
          ),
          _TabConfig(
            widget.i18n.t('profile'),
            Icons.person_rounded,
            _profile(),
          ),
        ];
    }
  }

  Widget _farmerDashboard() {
    return RefreshIndicator(
      onRefresh: () async =>
          Future<void>.delayed(const Duration(milliseconds: 700)),
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Good Morning, ${_dashboard?.greetingName.isNotEmpty == true ? _dashboard!.greetingName : widget.session.name}',
            style: Theme.of(context).textTheme.headlineMedium,
          ),
          const SizedBox(height: 12),
          _premiumBanner(
            title: _dashboard?.summaryTitle ?? 'Smart Farm Summary',
            subtitle:
                _dashboard?.summarySubtitle ??
                'Yield confidence: High · Compliance: Up to date',
            icon: Icons.eco_rounded,
          ),
          const SizedBox(height: 12),
          GlassCard(
            child: Row(
              children: [
                TweenAnimationBuilder<double>(
                  tween: Tween(begin: 0, end: math.pi * 2),
                  duration: const Duration(seconds: 12),
                  builder: (_, angle, child) =>
                      Transform.rotate(angle: angle, child: child),
                  child: const Icon(
                    Icons.wb_sunny_rounded,
                    color: AppPalette.warningAmber,
                    size: 30,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _dashboard?.weatherText ??
                        '31°C · Light breeze · Clouds moving',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          GlassCard(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Price Prediction'),
                const SizedBox(height: 10),
                SizedBox(
                  height: 88,
                  child: CustomPaint(painter: _LineChartPainter()),
                ),
                const SizedBox(height: 8),
                Row(
                  children: [
                    const Icon(
                      Icons.trending_up_rounded,
                      color: AppPalette.brandGreen,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _dashboard?.pricePredictionText ??
                            'Tomato up 6% tomorrow',
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),
          GlassCard(
            child: Row(
              children: [
                SizedBox(
                  width: 86,
                  height: 86,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      CircularProgressIndicator(
                        value: ((_dashboard?.freshnessScore ?? 86) / 100).clamp(
                          0.0,
                          1.0,
                        ),
                        strokeWidth: 8,
                        color: AppPalette.brandGreen,
                      ),
                      Text(
                        '${_dashboard?.freshnessScore ?? 86}',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
                          fontFamily: 'Space Grotesk',
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 14),
                const Expanded(child: Text('AI Freshness Score')),
              ],
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              _actionButton('Create Batch', Icons.add_box_outlined, () {
                Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const CreateBatchScreen()),
                );
              }),
              _actionButton(
                'Upload Certificate',
                Icons.file_upload_outlined,
                () {},
              ),
              _actionButton('View Trust Score', Icons.query_stats_rounded, () {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Trust Score increased to 82')),
                );
              }),
            ],
          ),
          const SizedBox(height: 88),
        ],
      ),
    );
  }

  Widget _myBatches() {
    final batchItems =
        _dashboard?.recentBatches ?? const <DashboardBatchItem>[];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _premiumBanner(
          title: 'Batch Operations',
          subtitle:
              'Active: ${_dashboard?.activeBatchesCount ?? 0} · Pending: ${_dashboard?.pendingTransfersCount ?? 0}',
          icon: Icons.inventory_2_rounded,
        ),
        const SizedBox(height: 12),
        if (batchItems.isEmpty)
          _batchCard(
            id: 'No batches yet',
            subtitle: 'Create your first batch to view live data.',
            icon: Icons.inventory_2_rounded,
            actionLabel: 'Create',
            primary: true,
          )
        else
          ...batchItems.take(5).toList().asMap().entries.map((entry) {
            final index = entry.key;
            final item = entry.value;
            return Padding(
              padding: EdgeInsets.only(bottom: index == 4 ? 0 : 12),
              child: _batchCard(
                id: item.batchCode,
                subtitle:
                    '${item.cropType} · ${item.quantity} · ${item.status}',
                icon: item.status == 'in_transit'
                    ? Icons.local_shipping_rounded
                    : Icons.eco_rounded,
                actionLabel: item.status == 'in_transit' ? 'Track' : 'Details',
                primary: index == 0,
              ),
            );
          }),
      ],
    );
  }

  Widget _batchCard({
    required String id,
    required String subtitle,
    required IconData icon,
    required String actionLabel,
    required bool primary,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return GlassCard(
      child: Row(
        children: [
          Container(
            width: 46,
            height: 46,
            decoration: BoxDecoration(
              color: isDark
                  ? AppPalette.darkSelected
                  : AppPalette.lightSelected,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(id, style: Theme.of(context).textTheme.titleMedium),
                const SizedBox(height: 4),
                Text(subtitle),
              ],
            ),
          ),
          const SizedBox(width: 10),
          SizedBox(
            width: 94,
            child: primary
                ? FilledButton(onPressed: () {}, child: Text(actionLabel))
                : OutlinedButton(onPressed: () {}, child: Text(actionLabel)),
          ),
        ],
      ),
    );
  }

  Widget _distributorDashboard() {
    final alertItems = _dashboard?.alerts ?? const <String>[];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _premiumBanner(
          title: _dashboard?.summaryTitle ?? 'Distribution Control',
          subtitle:
              _dashboard?.summarySubtitle ??
              'Vehicles available: 18/24 · Route health: Stable',
          icon: Icons.local_shipping_rounded,
        ),
        const SizedBox(height: 12),
        _metricCard('Warehouse Capacity', '66%'),
        const SizedBox(height: 12),
        if (alertItems.isEmpty)
          _alertCard('No live alerts right now')
        else
          ...alertItems.take(3).toList().asMap().entries.map((entry) {
            return Padding(
              padding: EdgeInsets.only(bottom: entry.key == 2 ? 0 : 12),
              child: _alertCard(entry.value),
            );
          }),
      ],
    );
  }

  Widget _activeShipments() {
    double sliderValue = 0;
    return StatefulBuilder(
      builder: (context, setStateLocal) {
        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _premiumBanner(
              title: 'Shipment #0x7829',
              subtitle: 'Temperature stable · Location: Tumakuru',
              icon: Icons.route_rounded,
            ),
            const SizedBox(height: 12),
            GlassCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Slide to Confirm Transfer'),
                  Slider(
                    value: sliderValue,
                    onChanged: (value) {
                      setStateLocal(() => sliderValue = value);
                      if (value > 0.96) {
                        setStateLocal(() => sliderValue = 0);
                        HapticFeedback.mediumImpact();
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Transfer confirmed')),
                        );
                      }
                    },
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _storage() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _metricCard('Cold Storage A1', '52%'),
        const SizedBox(height: 12),
        _metricCard('Cold Storage B2', '41%'),
      ],
    );
  }

  Widget _inventory() {
    final items =
        _dashboard?.inventoryItems ?? const <DashboardInventoryItem>[];
    return GridView.count(
      padding: const EdgeInsets.all(16),
      crossAxisCount: 2,
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 0.95,
      children: List.generate(items.isEmpty ? 4 : items.length, (index) {
        final item = items.isEmpty
            ? DashboardInventoryItem(
                name: 'Product ${index + 1}',
                demandSignal: 'AI demand ↑',
                expiryHint: index.isEven
                    ? 'Expires in 2 days'
                    : 'Expires in 5 days',
              )
            : items[index];
        final expiring =
            item.expiryHint.contains('2') || item.expiryHint.contains('1');
        return GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(item.name, style: Theme.of(context).textTheme.titleMedium),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  color: Theme.of(context).brightness == Brightness.dark
                      ? AppPalette.darkSelected
                      : AppPalette.lightSelected,
                ),
                child: Text(item.demandSignal),
              ),
              const SizedBox(height: 8),
              Text(
                item.expiryHint,
                style: TextStyle(
                  color: expiring ? Colors.redAccent : AppPalette.brandGreen,
                ),
              ),
            ],
          ),
        );
      }),
    );
  }

  Widget _incoming() {
    final incoming = _dashboard?.recentBatches ?? const <DashboardBatchItem>[];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (incoming.isEmpty)
          _batchCard(
            id: 'No incoming batches',
            subtitle: 'Live incoming data will appear here',
            icon: Icons.move_down_rounded,
            actionLabel: 'Refresh',
            primary: true,
          )
        else
          ...incoming
              .take(3)
              .map(
                (item) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: _batchCard(
                    id: item.batchCode,
                    subtitle: '${item.cropType} · ${item.status}',
                    icon: Icons.move_down_rounded,
                    actionLabel: 'View',
                    primary: true,
                  ),
                ),
              ),
      ],
    );
  }

  Widget _scanScreen() {
    return Stack(
      children: [
        Positioned.fill(child: Container(color: Colors.black)),
        Center(
          child: Hero(
            tag: 'product-hero',
            child: Container(
              width: 230,
              height: 230,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: AppPalette.accentGold, width: 3),
              ),
              child: const Center(
                child: Icon(
                  Icons.qr_code_2_rounded,
                  size: 76,
                  color: AppPalette.accentGold,
                ),
              ),
            ),
          ),
        ),
        Positioned(
          left: 16,
          right: 16,
          bottom: 28,
          child: FilledButton.icon(
            onPressed: () {
              Navigator.of(context).push(
                MaterialPageRoute(builder: (_) => const ProductJourneyScreen()),
              );
            },
            icon: const Icon(Icons.center_focus_strong_rounded),
            label: const Text('Simulate QR Scan'),
          ),
        ),
      ],
    );
  }

  Widget _explore() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _premiumBanner(
          title: 'Market Intelligence',
          subtitle: 'Tomato prices predicted to rise tomorrow',
          icon: Icons.auto_graph_rounded,
        ),
      ],
    );
  }

  Widget _orders() {
    final orders = _dashboard?.orders ?? const <String>[];
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        if (orders.isEmpty)
          GlassCard(
            child: Row(
              children: [
                Container(
                  width: 44,
                  height: 44,
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(10),
                    color: Theme.of(context).brightness == Brightness.dark
                        ? AppPalette.darkSelected
                        : AppPalette.lightSelected,
                  ),
                  child: const Icon(Icons.verified_rounded),
                ),
                const SizedBox(width: 12),
                const Expanded(child: Text('No live orders yet')),
              ],
            ),
          )
        else
          ...orders
              .take(3)
              .map(
                (order) => Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: GlassCard(
                    child: Row(
                      children: [
                        Container(
                          width: 44,
                          height: 44,
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(10),
                            color:
                                Theme.of(context).brightness == Brightness.dark
                                ? AppPalette.darkSelected
                                : AppPalette.lightSelected,
                          ),
                          child: const Icon(Icons.verified_rounded),
                        ),
                        const SizedBox(width: 12),
                        Expanded(child: Text(order)),
                      ],
                    ),
                  ),
                ),
              ),
      ],
    );
  }

  Widget _aiInsights() {
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _premiumBanner(
          title: 'AI Insights',
          subtitle: 'Prediction confidence and recommended actions',
          icon: Icons.insights_rounded,
        ),
        const SizedBox(height: 12),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Prediction Trend'),
              const SizedBox(height: 10),
              SizedBox(
                height: 90,
                child: CustomPaint(painter: _LineChartPainter()),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  const Text('Confidence'),
                  const SizedBox(width: 10),
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: LinearProgressIndicator(
                        value: ((_dashboard?.freshnessScore ?? 84) / 100).clamp(
                          0.0,
                          1.0,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),
        _alertCard(
          _dashboard?.alerts.isNotEmpty == true
              ? _dashboard!.alerts.first
              : 'Spoilage alert: humidity exceeded in lot #18',
        ),
        const SizedBox(height: 12),
        GlassCard(
          child: Text(
            _dashboard?.recommendation.isNotEmpty == true
                ? _dashboard!.recommendation
                : 'Recommended: shift lot #18 to cold storage B and dispatch within 6h.',
          ),
        ),
      ],
    );
  }

  Widget _profile() {
    final isDark = widget.themeMode == ThemeMode.dark;
    final langs = const {'English': 'en', 'हिन्दी': 'hi', 'தமிழ்': 'ta'};
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _premiumBanner(
          title: 'Profile & Security',
          subtitle: widget.session.isVerified
              ? 'Verification complete · Wallet linked'
              : 'Verification pending · Wallet linked',
          icon: Icons.verified_user_rounded,
        ),
        const SizedBox(height: 12),
        GlassCard(
          child: Column(
            children: [
              _profileRow(
                widget.i18n.t('verification_status'),
                widget.session.isVerified ? 'Verified' : 'Pending',
                icon: Icons.check_circle_rounded,
              ),
              _profileRow(
                widget.i18n.t('wallet_address'),
                widget.session.walletAddress,
                icon: Icons.account_balance_wallet_rounded,
              ),
              _profileRow(
                'Name',
                widget.session.name,
                icon: Icons.person_rounded,
              ),
              _profileRow(
                'Phone',
                widget.session.phone,
                icon: Icons.phone_rounded,
              ),
              _profileRow(
                'Role',
                widget.session.role.title,
                icon: Icons.badge_rounded,
              ),
              _profileRow(
                widget.i18n.t('trust_score'),
                '${_dashboard?.trustScore ?? 82}',
                icon: Icons.shield_rounded,
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Expanded(child: Text(widget.i18n.t('language'))),
                  DropdownButton<String>(
                    value: widget.i18n.lang,
                    items: [
                      for (final item in langs.entries)
                        DropdownMenuItem(
                          value: item.value,
                          child: Text(item.key),
                        ),
                    ],
                    onChanged: (value) {
                      if (value != null) widget.i18n.setLanguage(value);
                    },
                  ),
                ],
              ),
              SwitchListTile(
                contentPadding: EdgeInsets.zero,
                title: Text(widget.i18n.t('dark_mode')),
                value: isDark,
                onChanged: (value) => widget.onThemeModeChanged(
                  value ? ThemeMode.dark : ThemeMode.light,
                ),
              ),
              const SizedBox(height: 8),
              FilledButton.tonalIcon(
                onPressed: widget.onLogout,
                icon: const Icon(Icons.logout_rounded),
                label: Text(widget.i18n.t('logout')),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _profileRow(String label, String value, {required IconData icon}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Icon(icon, size: 18),
          const SizedBox(width: 8),
          Expanded(
            flex: 4,
            child: Text(label, maxLines: 1, overflow: TextOverflow.ellipsis),
          ),
          const SizedBox(width: 10),
          Expanded(
            flex: 6,
            child: Text(
              value,
              textAlign: TextAlign.right,
              maxLines: 2,
              softWrap: true,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontFamily: 'Space Grotesk',
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _actionButton(String label, IconData icon, VoidCallback onTap) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return SizedBox(
      width: 170,
      child: FilledButton.tonalIcon(
        onPressed: onTap,
        style: FilledButton.styleFrom(
          backgroundColor: isDark
              ? AppPalette.darkSurfaceAlt
              : AppPalette.lightSurfaceAlt,
          foregroundColor: Theme.of(context).colorScheme.onSurface,
          side: BorderSide(
            color: isDark ? AppPalette.darkBorder : AppPalette.lightBorder,
          ),
        ),
        icon: Icon(icon),
        label: Text(label),
      ),
    );
  }

  Widget _metricCard(String label, String value) {
    return GlassCard(
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(
            value,
            style: const TextStyle(
              fontFamily: 'Space Grotesk',
              fontSize: 22,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  Widget _alertCard(String message) {
    return GlassCard(
      child: Row(
        children: [
          const Icon(Icons.warning_amber_rounded, color: AppPalette.accentGold),
          const SizedBox(width: 10),
          Expanded(child: Text(message)),
        ],
      ),
    );
  }

  Widget _premiumBanner({
    required String title,
    required String subtitle,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [AppPalette.brandGreenDark, AppPalette.brandGreen],
        ),
        borderRadius: BorderRadius.circular(14),
      ),
      child: Row(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AppPalette.accentGold,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: const Color(0xFF241A07)),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: Theme.of(
                    context,
                  ).textTheme.titleMedium?.copyWith(color: Colors.white),
                ),
                const SizedBox(height: 2),
                Text(
                  subtitle,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: const Color(0xFFDEEEE7),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class CreateBatchScreen extends StatefulWidget {
  const CreateBatchScreen({super.key});

  @override
  State<CreateBatchScreen> createState() => _CreateBatchScreenState();
}

class _CreateBatchScreenState extends State<CreateBatchScreen> {
  int step = 0;
  final labels = const [
    'Crop Type',
    'Quantity',
    'Soil & Fertilizer Data',
    'Upload Metadata',
    'Confirm & Sign',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create Batch')),
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Step ${step + 1}/5',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(labels[step]),
                const SizedBox(height: 12),
                GlassCard(
                  child: SizedBox(
                    height: 150,
                    child: Center(
                      child: Text('Input section: ${labels[step]}'),
                    ),
                  ),
                ),
                const Spacer(),
                Row(
                  children: [
                    if (step > 0)
                      Expanded(
                        child: OutlinedButton(
                          onPressed: () => setState(() => step--),
                          child: const Text('Back'),
                        ),
                      ),
                    if (step > 0) const SizedBox(width: 10),
                    Expanded(
                      child: FilledButton(
                        onPressed: () async {
                          if (step < 4) {
                            setState(() => step++);
                            return;
                          }
                          HapticFeedback.mediumImpact();
                          await showDialog<void>(
                            context: context,
                            builder: (_) => AlertDialog(
                              title: const Text('Blockchain Confirmation'),
                              content: const Column(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  RotatingHexChain(),
                                  SizedBox(height: 12),
                                  Text('Batch Successfully Minted'),
                                ],
                              ),
                              actions: [
                                TextButton(
                                  onPressed: () => Navigator.pop(context),
                                  child: const Text('Done'),
                                ),
                              ],
                            ),
                          );
                          if (!context.mounted) return;
                          Navigator.pop(context);
                        },
                        child: Text(step == 4 ? 'Mint Batch' : 'Continue'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TabConfig {
  _TabConfig(this.label, this.icon, this.page);

  final String label;
  final IconData icon;
  final Widget page;
}

class _LineChartPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = AppPalette.accentGold
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3;

    final path = Path()
      ..moveTo(0, size.height * 0.7)
      ..quadraticBezierTo(
        size.width * 0.2,
        size.height * 0.35,
        size.width * 0.45,
        size.height * 0.55,
      )
      ..quadraticBezierTo(
        size.width * 0.75,
        size.height * 0.8,
        size.width,
        size.height * 0.3,
      );

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _AiAssistantPage extends StatefulWidget {
  const _AiAssistantPage({required this.onSend, required this.roleTitle});

  final Future<String> Function(String message) onSend;
  final String roleTitle;

  @override
  State<_AiAssistantPage> createState() => _AiAssistantPageState();
}

class _AiAssistantPageState extends State<_AiAssistantPage> {
  final TextEditingController _controller = TextEditingController();
  final List<_AiMessage> _messages = [];
  bool _isSending = false;

  @override
  void initState() {
    super.initState();
    _messages.add(
      _AiMessage(
        text:
            'AGRICHAIN AI is ready for ${widget.roleTitle}. Ask anything about pricing, yield, logistics, or traceability.',
        isUser: false,
      ),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    if (_isSending) {
      return;
    }
    final text = _controller.text.trim();
    if (text.isEmpty) {
      return;
    }

    setState(() {
      _messages.add(_AiMessage(text: text, isUser: true));
      _controller.clear();
      _isSending = true;
    });

    final reply = await widget.onSend(text);
    if (!mounted) {
      return;
    }
    setState(() {
      _messages.add(_AiMessage(text: reply, isUser: false));
      _isSending = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.viewInsetsOf(context).bottom;
    return Scaffold(
      appBar: AppBar(title: const Text('AI Assistant')),
      body: SafeArea(
        child: AnimatedPadding(
          duration: const Duration(milliseconds: 180),
          curve: Curves.easeOut,
          padding: EdgeInsets.only(bottom: bottomInset),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(16, 16, 16, 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'AGRICHAIN AI - ${widget.roleTitle}',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 10),
                Expanded(
                  child: ListView.separated(
                    itemCount: _messages.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final item = _messages[index];
                      final align = item.isUser
                          ? Alignment.centerRight
                          : Alignment.centerLeft;
                      final bg = item.isUser
                          ? Theme.of(context).colorScheme.primary
                          : Theme.of(
                              context,
                            ).colorScheme.surfaceContainerHighest;
                      final fg = item.isUser
                          ? Theme.of(context).colorScheme.onPrimary
                          : Theme.of(context).colorScheme.onSurface;
                      return Align(
                        alignment: align,
                        child: Container(
                          constraints: const BoxConstraints(maxWidth: 320),
                          padding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 10,
                          ),
                          decoration: BoxDecoration(
                            color: bg,
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Text(item.text, style: TextStyle(color: fg)),
                        ),
                      );
                    },
                  ),
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _controller,
                        textInputAction: TextInputAction.send,
                        onSubmitted: (_) => _send(),
                        decoration: const InputDecoration(
                          hintText: 'Ask AI... ',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    SizedBox(
                      width: 92,
                      child: FilledButton(
                        style: FilledButton.styleFrom(
                          minimumSize: const Size(0, 48),
                          maximumSize: const Size(120, 48),
                        ),
                        onPressed: _isSending ? null : _send,
                        child: Text(_isSending ? '...' : 'Send'),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _AiMessage {
  const _AiMessage({required this.text, required this.isUser});

  final String text;
  final bool isUser;
}
