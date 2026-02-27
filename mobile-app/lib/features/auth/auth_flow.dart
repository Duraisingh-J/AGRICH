import 'dart:convert';
import 'dart:developer' as developer;

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

import '../../core/i18n.dart';
import '../../core/models.dart';
import '../common/widgets.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key, required this.tagline});

  final String tagline;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const LeafLoader(size: 80),
                const SizedBox(height: 16),
                Text(
                  'AGRICHAIN',
                  style: Theme.of(context).textTheme.headlineMedium,
                ),
                const SizedBox(height: 8),
                Text(tagline, style: Theme.of(context).textTheme.bodyLarge),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class AuthFlow extends StatefulWidget {
  const AuthFlow({
    super.key,
    required this.onAuthenticated,
    required this.i18n,
  });

  final ValueChanged<AuthSession> onAuthenticated;
  final I18nController i18n;

  @override
  State<AuthFlow> createState() => _AuthFlowState();
}

class _AuthFlowState extends State<AuthFlow> {
  static const String _backendOtpBaseUrl = String.fromEnvironment(
    'BACKEND_OTP_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000/api/v1',
  );
  static const String _backendOtpBaseUrls = String.fromEnvironment(
    'BACKEND_OTP_BASE_URLS',
    defaultValue:
        'http://127.0.0.1:8000/api/v1,http://10.0.2.2:8000/api/v1,http://localhost:8000/api/v1',
  );

  int _step = 0;
  AppRole? _selectedRole;
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _otpController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _confirmPasswordController =
      TextEditingController();
  bool _isRequestingOtp = false;
  bool _isVerifyingOtp = false;
  bool _isFinishing = false;
  bool _usingBackendOtp = false;
  String? _activeBackendBaseUrl;

  @override
  void dispose() {
    _nameController.dispose();
    _phoneController.dispose();
    _otpController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: AnimatedGradientBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: AnimatedSwitcher(
              duration: const Duration(milliseconds: 280),
              transitionBuilder: (child, animation) {
                return FadeTransition(
                  opacity: animation,
                  child: SlideTransition(
                    position: Tween<Offset>(
                      begin: const Offset(0, 0.04),
                      end: Offset.zero,
                    ).animate(animation),
                    child: child,
                  ),
                );
              },
              child: _buildByStep(context),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildByStep(BuildContext context) {
    switch (_step) {
      case 0:
        return _roleSelectionStep(context);
      case 1:
        return _profileAndPhoneStep(context);
      case 2:
        return _otpVerificationStep(context);
      case 3:
        return _passwordSetupStep(context);
      default:
        return _roleSelectionStep(context);
    }
  }

  Widget _roleSelectionStep(BuildContext context) {
    return Column(
      key: const ValueKey('role-selection-step'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Select your ecosystem',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 16),
        Expanded(
          child: GridView.count(
            crossAxisCount: 2,
            crossAxisSpacing: 16,
            mainAxisSpacing: 16,
            children: AppRole.values.map((role) {
              final isSelected = _selectedRole == role;
              return InkWell(
                borderRadius: BorderRadius.circular(16),
                onTap: () => setState(() => _selectedRole = role),
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 180),
                  decoration: BoxDecoration(
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: isSelected
                          ? Theme.of(context).colorScheme.primary
                          : Colors.transparent,
                      width: 1.8,
                    ),
                  ),
                  child: GlassCard(
                    padding: const EdgeInsets.all(14),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Icon(
                          role.icon,
                          size: 32,
                          color: Theme.of(context).colorScheme.primary,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          role.title,
                          style: Theme.of(context).textTheme.titleMedium,
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          child: FilledButton(
            onPressed: _selectedRole == null
                ? null
                : () => setState(() => _step = 1),
            child: const Text('Continue'),
          ),
        ),
      ],
    );
  }

  Widget _profileAndPhoneStep(BuildContext context) {
    final canContinue =
        _nameController.text.trim().isNotEmpty &&
        _phoneController.text.trim().length >= 10 &&
        !_isRequestingOtp;

    return Column(
      key: const ValueKey('profile-phone-step'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '${_selectedRole?.title ?? 'User'} Onboarding',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 8),
        Text(
          'Enter first name and mobile number to receive OTP.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 16),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: _nameController,
                textInputAction: TextInputAction.next,
                autofillHints: const [AutofillHints.givenName],
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  labelText: 'First Name',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _phoneController,
                keyboardType: TextInputType.phone,
                textInputAction: TextInputAction.done,
                autofillHints: const [AutofillHints.telephoneNumber],
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  labelText: 'Mobile Number',
                  border: OutlineInputBorder(),
                  prefixText: '+91 ',
                ),
              ),
            ],
          ),
        ),
        const Spacer(),
        SizedBox(
          width: double.infinity,
          child: FilledButton(
            onPressed: canContinue ? _requestOtp : null,
            child: Text(_isRequestingOtp ? 'Sending OTP...' : 'Send OTP'),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton(
            onPressed: () => setState(() => _step = 0),
            child: const Text('Back'),
          ),
        ),
      ],
    );
  }

  Widget _otpVerificationStep(BuildContext context) {
    return Column(
      key: const ValueKey('otp-verification-step'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'OTP Verification',
          style: Theme.of(context).textTheme.headlineMedium,
        ),
        const SizedBox(height: 8),
        Text(
          'Enter the 6-digit OTP sent to ${_displayPhoneNumber()}.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 16),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: _otpController,
                maxLength: 6,
                keyboardType: TextInputType.number,
                textInputAction: TextInputAction.done,
                autofillHints: const [AutofillHints.oneTimeCode],
                onChanged: (value) {
                  setState(() {});
                  if (value.length == 6) {
                    FocusScope.of(context).unfocus();
                  }
                },
                decoration: const InputDecoration(
                  labelText: 'Enter OTP',
                  border: OutlineInputBorder(),
                  counterText: '',
                ),
              ),
              const SizedBox(height: 8),
              TextButton(
                onPressed: _isRequestingOtp ? null : _requestOtp,
                child: Text(_isRequestingOtp ? 'Resending...' : 'Resend OTP'),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        const Spacer(),
        SizedBox(
          width: double.infinity,
          child: FilledButton.icon(
            onPressed: _otpController.text.length == 6 && !_isVerifyingOtp
                ? _verifyOtp
                : null,
            icon: const Icon(Icons.verified_user_rounded),
            label: Text(_isVerifyingOtp ? 'Verifying...' : 'Verify OTP'),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton(
            onPressed: () => setState(() => _step = 1),
            child: const Text('Back'),
          ),
        ),
      ],
    );
  }

  Widget _passwordSetupStep(BuildContext context) {
    final password = _passwordController.text;
    final confirm = _confirmPasswordController.text;
    final isValid = password.length >= 6 && password == confirm;

    return Column(
      key: const ValueKey('password-step'),
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Set Password', style: Theme.of(context).textTheme.headlineMedium),
        const SizedBox(height: 8),
        Text(
          'Create a password after OTP verification.',
          style: Theme.of(context).textTheme.bodyMedium,
        ),
        const SizedBox(height: 16),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              TextField(
                controller: _passwordController,
                obscureText: true,
                textInputAction: TextInputAction.next,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  labelText: 'Password',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: _confirmPasswordController,
                obscureText: true,
                textInputAction: TextInputAction.done,
                onChanged: (_) => setState(() {}),
                decoration: const InputDecoration(
                  labelText: 'Confirm Password',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
        const Spacer(),
        SizedBox(
          width: double.infinity,
          child: FilledButton(
            onPressed: isValid && !_isFinishing ? _finishOnboarding : null,
            child: Text(_isFinishing ? 'Signing in...' : 'Continue'),
          ),
        ),
        const SizedBox(height: 8),
        SizedBox(
          width: double.infinity,
          child: OutlinedButton(
            onPressed: () => setState(() => _step = 2),
            child: const Text('Back'),
          ),
        ),
      ],
    );
  }

  String _displayPhoneNumber() {
    final input = _phoneController.text.trim();
    if (input.startsWith('+')) {
      return input;
    }
    return '+91 $input';
  }

  String _normalizePhoneForOtp() {
    final digitsOnly = _phoneController.text.replaceAll(RegExp(r'\D'), '');
    if (_phoneController.text.trim().startsWith('+')) {
      return _phoneController.text.trim();
    }
    if (digitsOnly.length == 10) {
      return '+91$digitsOnly';
    }
    return '+$digitsOnly';
  }

  Future<void> _requestOtp() async {
    if (_isRequestingOtp) {
      return;
    }

    setState(() => _isRequestingOtp = true);

    final backendOk = await _requestOtpFromBackend();
    if (backendOk) {
      return;
    }
    if (!mounted) {
      return;
    }
    setState(() => _isRequestingOtp = false);
    _showSnack(
      'Unable to reach backend OTP service. If using USB device, run adb reverse tcp:8000 tcp:8000, then retry.',
    );
  }

  Future<void> _verifyOtp() async {
    if (_isVerifyingOtp) {
      return;
    }

    setState(() => _isVerifyingOtp = true);

    if (_usingBackendOtp) {
      final verified = await _verifyOtpWithBackend();
      if (!verified && mounted) {
        setState(() => _isVerifyingOtp = false);
      }
      return;
    }

    setState(() => _isVerifyingOtp = false);
    _showSnack('Request OTP first.');
  }

  Future<bool> _requestOtpFromBackend() async {
    final candidates = _backendBaseUrlCandidates();
    developer.log('Requesting OTP from backend. Candidates: $candidates');

    for (final baseUrl in candidates) {
      try {
        final url = _apiUrl(baseUrl, '/auth/otp/request');
        developer.log('Trying OTP request to: $url');

        final response = await http
            .post(
              Uri.parse(url),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({'phone': _normalizePhoneForOtp()}),
            )
            .timeout(const Duration(seconds: 15));

        developer.log('OTP response from $baseUrl: ${response.statusCode}');

        if (!mounted) {
          return false;
        }

        if (response.statusCode >= 200 && response.statusCode < 300) {
          final body = jsonDecode(response.body) as Map<String, dynamic>;
          final debugOtp = body['debug_otp']?.toString();
          setState(() {
            _isRequestingOtp = false;
            _usingBackendOtp = true;
            _activeBackendBaseUrl = baseUrl;
            _step = 2;
          });
          if (debugOtp != null && debugOtp.isNotEmpty) {
            _showSnack('Backend OTP sent. Debug OTP: $debugOtp');
          } else {
            _showSnack('Backend OTP sent successfully.');
          }
          return true;
        }
      } catch (e) {
        developer.log('OTP request failed for $baseUrl: $e');
        continue;
      }
    }

    developer.log('All backend OTP candidates failed.');
    return false;
  }

  Future<bool> _verifyOtpWithBackend() async {
    final candidates = _backendBaseUrlCandidates();
    developer.log('Verifying OTP with backend. Candidates: $candidates');

    for (final baseUrl in candidates) {
      try {
        final url = _apiUrl(baseUrl, '/auth/otp/verify');
        developer.log('Trying OTP verify to: $url');

        final response = await http
            .post(
              Uri.parse(url),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({
                'phone': _normalizePhoneForOtp(),
                'otp': _otpController.text.trim(),
              }),
            )
            .timeout(const Duration(seconds: 15));

        developer.log(
          'OTP verify response from $baseUrl: ${response.statusCode}',
        );

        if (!mounted) {
          return false;
        }

        if (response.statusCode >= 200 && response.statusCode < 300) {
          setState(() {
            _isVerifyingOtp = false;
            _activeBackendBaseUrl = baseUrl;
            _step = 3;
          });
          _showSnack('OTP verified successfully.');
          return true;
        }
      } catch (e) {
        developer.log('OTP verify failed for $baseUrl: $e');
        continue;
      }
    }

    _showSnack('Backend OTP verification failed. Please check OTP and retry.');
    return false;
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

    addCandidate(_activeBackendBaseUrl ?? '');
    addCandidate(_backendOtpBaseUrl);
    for (final item in _backendOtpBaseUrls.split(',')) {
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

  Future<void> _finishOnboarding() async {
    if (_isFinishing || _selectedRole == null) {
      return;
    }
    setState(() => _isFinishing = true);
    final saved = await _saveOnboardingToBackend();
    if (!mounted) {
      return;
    }
    if (!saved) {
      setState(() => _isFinishing = false);
      return;
    }

    final session = await _loginWithBackend();
    if (!mounted) {
      return;
    }
    if (session == null) {
      setState(() => _isFinishing = false);
      _showSnack('Profile saved, but backend login failed. Please retry.');
      return;
    }

    setState(() => _isFinishing = false);
    widget.onAuthenticated(session);
  }

  Future<AuthSession?> _loginWithBackend() async {
    final candidates = _backendBaseUrlCandidates();
    developer.log('Logging in with backend. Candidates: $candidates');

    for (final baseUrl in candidates) {
      try {
        final url = _apiUrl(baseUrl, '/auth/mobile-login');
        developer.log('Trying mobile-login request to: $url');

        final response = await http
            .post(
              Uri.parse(url),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({
                'phone': _normalizePhoneForOtp(),
                'password': _passwordController.text,
              }),
            )
            .timeout(const Duration(seconds: 15));

        developer.log(
          'Mobile-login response from $baseUrl: ${response.statusCode}',
        );

        if (response.statusCode >= 200 && response.statusCode < 300) {
          final body = jsonDecode(response.body) as Map<String, dynamic>;
          _activeBackendBaseUrl = baseUrl;
          return AuthSession.fromBackendJson(body);
        }
      } catch (e) {
        developer.log('Mobile-login failed for $baseUrl: $e');
        continue;
      }
    }

    return null;
  }

  Future<bool> _saveOnboardingToBackend() async {
    final candidates = _backendBaseUrlCandidates();
    developer.log('Saving onboarding data. Candidates: $candidates');

    for (final baseUrl in candidates) {
      try {
        final url = _apiUrl(baseUrl, '/auth/onboard-mobile');
        developer.log('Trying onboard-mobile request to: $url');

        final response = await http
            .post(
              Uri.parse(url),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({
                'name': _nameController.text.trim(),
                'phone': _normalizePhoneForOtp(),
                'role': _selectedRole!.name,
                'password': _passwordController.text,
              }),
            )
            .timeout(const Duration(seconds: 15));

        developer.log('Onboard response from $baseUrl: ${response.statusCode}');

        if (response.statusCode >= 200 && response.statusCode < 300) {
          developer.log('Successfully saved onboarding data');
          return true;
        }
      } catch (e) {
        developer.log('Onboard request failed for $baseUrl: $e');
        continue;
      }
    }

    _showSnack('Unable to save profile to backend. Please try again.');
    return false;
  }

  void _showSnack(String message) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }
}
