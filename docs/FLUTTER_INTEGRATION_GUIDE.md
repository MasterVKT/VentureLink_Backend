# Guide d'intégration Flutter - VentureLink API

## Vue d'ensemble

Ce guide explique comment intégrer l'API VentureLink dans une application Flutter, avec des exemples concrets et les bonnes pratiques recommandées.

## Configuration du projet

### Dépendances requises

Ajoutez ces dépendances dans votre `pubspec.yaml` :

```yaml
dependencies:
  http: ^1.1.0
  dio: ^5.3.2  # Alternative recommandée à http
  json_annotation: ^4.8.1
  shared_preferences: ^2.2.2
  flutter_secure_storage: ^9.0.0
  connectivity_plus: ^5.0.2
  cached_network_image: ^3.3.0
  file_picker: ^6.1.1

dev_dependencies:
  json_serializable: ^6.7.1
  build_runner: ^2.4.7
```

### Configuration de l'API

Créez un fichier `lib/services/api_config.dart` :

```dart
class ApiConfig {
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000',
  );
  
  static const String apiVersion = 'v1';
  static const String apiPrefix = '/api/$apiVersion';
  
  static String get fullBaseUrl => '$baseUrl$apiPrefix';
  
  // Endpoints
  static const String auth = '/auth';
  static const String users = '/users';
  static const String projects = '/projects';
  static const String investments = '/investments';
  static const String conversations = '/conversations';
  static const String notifications = '/notifications';
}
```

## Gestion de l'authentification

### Modèle Token

```dart
// lib/models/auth/token_model.dart
import 'package:json_annotation/json_annotation.dart';

part 'token_model.g.dart';

@JsonSerializable()
class TokenModel {
  final String access;
  final String refresh;

  TokenModel({
    required this.access,
    required this.refresh,
  });

  factory TokenModel.fromJson(Map<String, dynamic> json) =>
      _$TokenModelFromJson(json);

  Map<String, dynamic> toJson() => _$TokenModelToJson(this);
}
```

### Service d'authentification

```dart
// lib/services/auth_service.dart
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../models/auth/token_model.dart';
import '../models/user/user_model.dart';
import 'api_config.dart';

class AuthService {
  static const _storage = FlutterSecureStorage();
  static const _accessTokenKey = 'access_token';
  static const _refreshTokenKey = 'refresh_token';
  
  final Dio _dio = Dio();

  AuthService() {
    _dio.options.baseUrl = ApiConfig.fullBaseUrl;
    _dio.interceptors.add(_createAuthInterceptor());
  }

  // Inscription
  Future<AuthResult> register({
    required String email,
    required String firstName,
    required String lastName,
    required String password,
    required String passwordConfirmation,
    required String userType,
  }) async {
    try {
      final response = await _dio.post(
        '${ApiConfig.auth}/register/',
        data: {
          'email': email,
          'first_name': firstName,
          'last_name': lastName,
          'password': password,
          'password_confirmation': passwordConfirmation,
          'user_type': userType,
          'terms_accepted': true,
        },
      );

      final tokens = TokenModel.fromJson(response.data['tokens']);
      final user = UserModel.fromJson(response.data['user']);
      
      await _saveTokens(tokens);
      
      return AuthResult.success(user: user, tokens: tokens);
    } on DioException catch (e) {
      return AuthResult.failure(_handleDioError(e));
    }
  }

  // Connexion
  Future<AuthResult> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        '${ApiConfig.auth}/token/',
        data: {
          'email': email,
          'password': password,
        },
      );

      final tokens = TokenModel.fromJson({
        'access': response.data['access'],
        'refresh': response.data['refresh'],
      });
      
      final user = UserModel.fromJson(response.data['user']);
      
      await _saveTokens(tokens);
      
      return AuthResult.success(user: user, tokens: tokens);
    } on DioException catch (e) {
      return AuthResult.failure(_handleDioError(e));
    }
  }

  // Rafraîchissement du token
  Future<bool> refreshToken() async {
    try {
      final refreshToken = await _storage.read(key: _refreshTokenKey);
      if (refreshToken == null) return false;

      final response = await _dio.post(
        '${ApiConfig.auth}/token/refresh/',
        data: {'refresh': refreshToken},
      );

      final tokens = TokenModel.fromJson({
        'access': response.data['access'],
        'refresh': response.data['refresh'] ?? refreshToken,
      });

      await _saveTokens(tokens);
      return true;
    } catch (e) {
      await logout();
      return false;
    }
  }

  // Déconnexion
  Future<void> logout() async {
    try {
      await _dio.post('${ApiConfig.auth}/logout/');
    } catch (e) {
      // Ignore l'erreur de déconnexion côté serveur
    } finally {
      await _storage.delete(key: _accessTokenKey);
      await _storage.delete(key: _refreshTokenKey);
    }
  }

  // Vérifier si l'utilisateur est connecté
  Future<bool> isLoggedIn() async {
    final accessToken = await _storage.read(key: _accessTokenKey);
    return accessToken != null;
  }

  // Obtenir le token d'accès
  Future<String?> getAccessToken() async {
    return await _storage.read(key: _accessTokenKey);
  }

  // Sauvegarder les tokens
  Future<void> _saveTokens(TokenModel tokens) async {
    await _storage.write(key: _accessTokenKey, value: tokens.access);
    await _storage.write(key: _refreshTokenKey, value: tokens.refresh);
  }

  // Intercepteur pour l'authentification automatique
  Interceptor _createAuthInterceptor() {
    return InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await getAccessToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        options.headers['Content-Type'] = 'application/json';
        options.headers['Accept'] = 'application/json';
        handler.next(options);
      },
      onError: (DioException error, handler) async {
        if (error.response?.statusCode == 401) {
          // Token expiré, essayer de le rafraîchir
          final refreshed = await refreshToken();
          if (refreshed) {
            // Rejouer la requête avec le nouveau token
            final options = error.requestOptions;
            final token = await getAccessToken();
            options.headers['Authorization'] = 'Bearer $token';
            
            try {
              final response = await _dio.request(
                options.path,
                options: Options(
                  method: options.method,
                  headers: options.headers,
                ),
                data: options.data,
                queryParameters: options.queryParameters,
              );
              handler.resolve(response);
              return;
            } catch (e) {
              // La nouvelle requête a échoué
            }
          }
          
          // Impossible de rafraîchir, déconnecter
          await logout();
        }
        handler.next(error);
      },
    );
  }

  String _handleDioError(DioException error) {
    if (error.response?.data != null) {
      final data = error.response!.data;
      if (data is Map<String, dynamic> && data.containsKey('error')) {
        return data['error']['message'] ?? 'Erreur inconnue';
      }
    }
    return error.message ?? 'Erreur de connexion';
  }
}

// Classe de résultat d'authentification
class AuthResult {
  final bool isSuccess;
  final UserModel? user;
  final TokenModel? tokens;
  final String? error;

  AuthResult._({
    required this.isSuccess,
    this.user,
    this.tokens,
    this.error,
  });

  factory AuthResult.success({
    required UserModel user,
    required TokenModel tokens,
  }) =>
      AuthResult._(
        isSuccess: true,
        user: user,
        tokens: tokens,
      );

  factory AuthResult.failure(String error) =>
      AuthResult._(
        isSuccess: false,
        error: error,
      );
}
```

## Modèles de données

### Modèle utilisateur

```dart
// lib/models/user/user_model.dart
import 'package:json_annotation/json_annotation.dart';

part 'user_model.g.dart';

@JsonSerializable()
class UserModel {
  final String id;
  final String email;
  @JsonKey(name: 'first_name')
  final String firstName;
  @JsonKey(name: 'last_name')
  final String lastName;
  @JsonKey(name: 'user_type')
  final String userType;
  @JsonKey(name: 'phone_number')
  final String? phoneNumber;
  final String? location;
  final String language;
  @JsonKey(name: 'preferred_currency')
  final String preferredCurrency;
  @JsonKey(name: 'is_verified')
  final bool isVerified;
  @JsonKey(name: 'is_premium')
  final bool isPremium;
  @JsonKey(name: 'fcm_token')
  final String? fcmToken;
  @JsonKey(name: 'date_joined')
  final DateTime dateJoined;

  UserModel({
    required this.id,
    required this.email,
    required this.firstName,
    required this.lastName,
    required this.userType,
    this.phoneNumber,
    this.location,
    required this.language,
    required this.preferredCurrency,
    required this.isVerified,
    required this.isPremium,
    this.fcmToken,
    required this.dateJoined,
  });

  factory UserModel.fromJson(Map<String, dynamic> json) =>
      _$UserModelFromJson(json);

  Map<String, dynamic> toJson() => _$UserModelToJson(this);

  String get fullName => '$firstName $lastName'.trim();
  
  bool get isInvestor => userType == 'INVESTOR' || userType == 'BOTH';
  bool get isProjectOwner => userType == 'PROJECT_OWNER' || userType == 'BOTH';
}
```

### Modèle projet

```dart
// lib/models/project/project_model.dart
import 'package:json_annotation/json_annotation.dart';
import '../user/user_model.dart';

part 'project_model.g.dart';

@JsonSerializable()
class ProjectModel {
  final String id;
  final String title;
  @JsonKey(name: 'short_description')
  final String shortDescription;
  @JsonKey(name: 'full_description')
  final String? fullDescription;
  final ProjectCategory category;
  final String stage;
  final String status;
  @JsonKey(name: 'funding_min')
  final double? fundingMin;
  @JsonKey(name: 'funding_max')
  final double? fundingMax;
  @JsonKey(name: 'funding_currency')
  final String fundingCurrency;
  @JsonKey(name: 'location_country')
  final String? locationCountry;
  @JsonKey(name: 'location_city')
  final String? locationCity;
  @JsonKey(name: 'is_premium')
  final bool isPremium;
  @JsonKey(name: 'is_featured')
  final bool isFeatured;
  @JsonKey(name: 'is_draft')
  final bool isDraft;
  @JsonKey(name: 'views_count')
  final int viewsCount;
  @JsonKey(name: 'interests_count')
  final int interestsCount;
  @JsonKey(name: 'favorites_count')
  final int favoritesCount;
  final UserModel creator;
  @JsonKey(name: 'primary_image')
  final String? primaryImage;
  final List<ProjectTag> tags;
  @JsonKey(name: 'created_at')
  final DateTime createdAt;
  @JsonKey(name: 'published_at')
  final DateTime? publishedAt;

  ProjectModel({
    required this.id,
    required this.title,
    required this.shortDescription,
    this.fullDescription,
    required this.category,
    required this.stage,
    required this.status,
    this.fundingMin,
    this.fundingMax,
    required this.fundingCurrency,
    this.locationCountry,
    this.locationCity,
    required this.isPremium,
    required this.isFeatured,
    required this.isDraft,
    required this.viewsCount,
    required this.interestsCount,
    required this.favoritesCount,
    required this.creator,
    this.primaryImage,
    required this.tags,
    required this.createdAt,
    this.publishedAt,
  });

  factory ProjectModel.fromJson(Map<String, dynamic> json) =>
      _$ProjectModelFromJson(json);

  Map<String, dynamic> toJson() => _$ProjectModelToJson(this);

  String get fundingRange {
    if (fundingMin == null && fundingMax == null) return 'Non spécifié';
    if (fundingMin == null) return 'Jusqu\'à ${fundingMax?.toStringAsFixed(0)} $fundingCurrency';
    if (fundingMax == null) return 'À partir de ${fundingMin?.toStringAsFixed(0)} $fundingCurrency';
    return '${fundingMin?.toStringAsFixed(0)} - ${fundingMax?.toStringAsFixed(0)} $fundingCurrency';
  }

  String get location {
    if (locationCity != null && locationCountry != null) {
      return '$locationCity, $locationCountry';
    }
    return locationCountry ?? locationCity ?? 'Non spécifié';
  }
}

@JsonSerializable()
class ProjectCategory {
  final String id;
  @JsonKey(name: 'name_fr')
  final String nameFr;
  @JsonKey(name: 'name_en')
  final String nameEn;
  final String? icon;

  ProjectCategory({
    required this.id,
    required this.nameFr,
    required this.nameEn,
    this.icon,
  });

  factory ProjectCategory.fromJson(Map<String, dynamic> json) =>
      _$ProjectCategoryFromJson(json);

  Map<String, dynamic> toJson() => _$ProjectCategoryToJson(this);
}

@JsonSerializable()
class ProjectTag {
  final String id;
  @JsonKey(name: 'name_fr')
  final String nameFr;
  @JsonKey(name: 'name_en')
  final String nameEn;

  ProjectTag({
    required this.id,
    required this.nameFr,
    required this.nameEn,
  });

  factory ProjectTag.fromJson(Map<String, dynamic> json) =>
      _$ProjectTagFromJson(json);

  Map<String, dynamic> toJson() => _$ProjectTagToJson(this);
}
```

## Services API

### Service Projets

```dart
// lib/services/project_service.dart
import 'package:dio/dio.dart';
import '../models/project/project_model.dart';
import '../models/common/paginated_response.dart';
import 'api_config.dart';

class ProjectService {
  final Dio _dio;

  ProjectService(this._dio);

  // Obtenir la liste des projets avec filtres
  Future<PaginatedResponse<ProjectModel>> getProjects({
    int page = 1,
    int pageSize = 20,
    String? category,
    String? stage,
    String? status,
    double? fundingMin,
    double? fundingMax,
    String? locationCountry,
    String? search,
    List<String>? tags,
    bool? isFeatured,
    String? ordering,
  }) async {
    try {
      final queryParameters = <String, dynamic>{
        'page': page,
        'page_size': pageSize,
      };

      if (category != null) queryParameters['category'] = category;
      if (stage != null) queryParameters['stage'] = stage;
      if (status != null) queryParameters['status'] = status;
      if (fundingMin != null) queryParameters['funding_min'] = fundingMin;
      if (fundingMax != null) queryParameters['funding_max'] = fundingMax;
      if (locationCountry != null) queryParameters['location_country'] = locationCountry;
      if (search != null) queryParameters['search'] = search;
      if (tags != null && tags.isNotEmpty) queryParameters['tags'] = tags.join(',');
      if (isFeatured != null) queryParameters['is_featured'] = isFeatured;
      if (ordering != null) queryParameters['ordering'] = ordering;

      final response = await _dio.get(
        '${ApiConfig.projects}/',
        queryParameters: queryParameters,
      );

      return PaginatedResponse<ProjectModel>.fromJson(
        response.data,
        (json) => ProjectModel.fromJson(json as Map<String, dynamic>),
      );
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Obtenir un projet par ID
  Future<ProjectModel> getProject(String projectId) async {
    try {
      final response = await _dio.get('${ApiConfig.projects}/$projectId/');
      return ProjectModel.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Créer un nouveau projet
  Future<ProjectModel> createProject({
    required String title,
    required String shortDescription,
    required String fullDescription,
    required String categoryId,
    required String stage,
    double? fundingMin,
    double? fundingMax,
    String? fundingCurrency,
    String? locationCountry,
    String? locationCity,
    List<String>? tagIds,
    bool isDraft = true,
  }) async {
    try {
      final data = <String, dynamic>{
        'title': title,
        'short_description': shortDescription,
        'full_description': fullDescription,
        'category': categoryId,
        'stage': stage,
        'is_draft': isDraft,
      };

      if (fundingMin != null) data['funding_min'] = fundingMin;
      if (fundingMax != null) data['funding_max'] = fundingMax;
      if (fundingCurrency != null) data['funding_currency'] = fundingCurrency;
      if (locationCountry != null) data['location_country'] = locationCountry;
      if (locationCity != null) data['location_city'] = locationCity;
      if (tagIds != null) data['tags'] = tagIds;

      final response = await _dio.post(
        '${ApiConfig.projects}/',
        data: data,
      );

      return ProjectModel.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Mettre à jour un projet
  Future<ProjectModel> updateProject(
    String projectId,
    Map<String, dynamic> data,
  ) async {
    try {
      final response = await _dio.patch(
        '${ApiConfig.projects}/$projectId/',
        data: data,
      );
      return ProjectModel.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Basculer le statut favori
  Future<void> toggleFavorite(String projectId) async {
    try {
      await _dio.post('${ApiConfig.projects}/$projectId/toggle_favorite/');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Exprimer un intérêt
  Future<void> toggleInterest(String projectId) async {
    try {
      await _dio.post('${ApiConfig.projects}/$projectId/toggle_interest/');
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  // Publier un projet
  Future<ProjectModel> publishProject(String projectId) async {
    try {
      final response = await _dio.post('${ApiConfig.projects}/$projectId/publish/');
      return ProjectModel.fromJson(response.data);
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  String _handleError(DioException error) {
    if (error.response?.data != null) {
      final data = error.response!.data;
      if (data is Map<String, dynamic> && data.containsKey('error')) {
        return data['error']['message'] ?? 'Erreur inconnue';
      }
    }
    return error.message ?? 'Erreur de connexion';
  }
}
```

## Gestion des états avec Provider

### Provider d'authentification

```dart
// lib/providers/auth_provider.dart
import 'package:flutter/foundation.dart';
import '../models/user/user_model.dart';
import '../services/auth_service.dart';

class AuthProvider extends ChangeNotifier {
  final AuthService _authService = AuthService();
  
  UserModel? _user;
  bool _isLoading = false;
  String? _error;

  UserModel? get user => _user;
  bool get isLoading => _isLoading;
  String? get error => _error;
  bool get isAuthenticated => _user != null;

  Future<void> checkAuthStatus() async {
    _setLoading(true);
    try {
      final isLoggedIn = await _authService.isLoggedIn();
      if (isLoggedIn) {
        // Récupérer les informations utilisateur
        // await getCurrentUser();
      }
    } catch (e) {
      _setError(e.toString());
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> login(String email, String password) async {
    _setLoading(true);
    _clearError();
    
    try {
      final result = await _authService.login(
        email: email,
        password: password,
      );
      
      if (result.isSuccess) {
        _user = result.user;
        notifyListeners();
        return true;
      } else {
        _setError(result.error ?? 'Erreur de connexion');
        return false;
      }
    } catch (e) {
      _setError(e.toString());
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<bool> register({
    required String email,
    required String firstName,
    required String lastName,
    required String password,
    required String passwordConfirmation,
    required String userType,
  }) async {
    _setLoading(true);
    _clearError();
    
    try {
      final result = await _authService.register(
        email: email,
        firstName: firstName,
        lastName: lastName,
        password: password,
        passwordConfirmation: passwordConfirmation,
        userType: userType,
      );
      
      if (result.isSuccess) {
        _user = result.user;
        notifyListeners();
        return true;
      } else {
        _setError(result.error ?? 'Erreur d\'inscription');
        return false;
      }
    } catch (e) {
      _setError(e.toString());
      return false;
    } finally {
      _setLoading(false);
    }
  }

  Future<void> logout() async {
    _setLoading(true);
    try {
      await _authService.logout();
      _user = null;
      notifyListeners();
    } catch (e) {
      _setError(e.toString());
    } finally {
      _setLoading(false);
    }
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _setError(String error) {
    _error = error;
    notifyListeners();
  }

  void _clearError() {
    _error = null;
    notifyListeners();
  }
}
```

## Widgets d'interface

### Widget de connexion

```dart
// lib/screens/auth/login_screen.dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/auth_provider.dart';

class LoginScreen extends StatefulWidget {
  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  bool _obscurePassword = true;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _login() async {
    if (!_formKey.currentState!.validate()) return;

    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    final success = await authProvider.login(
      _emailController.text.trim(),
      _passwordController.text,
    );

    if (success) {
      Navigator.of(context).pushReplacementNamed('/home');
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(authProvider.error ?? 'Erreur de connexion'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Connexion'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: SafeArea(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Logo
                Container(
                  height: 120,
                  child: Image.asset('assets/images/logo.png'),
                ),
                SizedBox(height: 32),
                
                // Email
                TextFormField(
                  controller: _emailController,
                  keyboardType: TextInputType.emailAddress,
                  decoration: InputDecoration(
                    labelText: 'Email',
                    prefixIcon: Icon(Icons.email),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Veuillez saisir votre email';
                    }
                    if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value)) {
                      return 'Email invalide';
                    }
                    return null;
                  },
                ),
                SizedBox(height: 16),
                
                // Mot de passe
                TextFormField(
                  controller: _passwordController,
                  obscureText: _obscurePassword,
                  decoration: InputDecoration(
                    labelText: 'Mot de passe',
                    prefixIcon: Icon(Icons.lock),
                    suffixIcon: IconButton(
                      icon: Icon(_obscurePassword ? Icons.visibility : Icons.visibility_off),
                      onPressed: () {
                        setState(() {
                          _obscurePassword = !_obscurePassword;
                        });
                      },
                    ),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Veuillez saisir votre mot de passe';
                    }
                    return null;
                  },
                ),
                SizedBox(height: 24),
                
                // Bouton de connexion
                Consumer<AuthProvider>(
                  builder: (context, authProvider, child) {
                    return ElevatedButton(
                      onPressed: authProvider.isLoading ? null : _login,
                      style: ElevatedButton.styleFrom(
                        padding: EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                      ),
                      child: authProvider.isLoading
                          ? CircularProgressIndicator(color: Colors.white)
                          : Text(
                              'Se connecter',
                              style: TextStyle(fontSize: 16),
                            ),
                    );
                  },
                ),
                
                SizedBox(height: 16),
                
                // Lien d'inscription
                TextButton(
                  onPressed: () {
                    Navigator.of(context).pushNamed('/register');
                  },
                  child: Text('Pas encore de compte ? S\'inscrire'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
```

### Widget de liste de projets

```dart
// lib/widgets/project/project_list.dart
import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../models/project/project_model.dart';

class ProjectList extends StatelessWidget {
  final List<ProjectModel> projects;
  final VoidCallback? onLoadMore;
  final bool isLoading;

  const ProjectList({
    Key? key,
    required this.projects,
    this.onLoadMore,
    this.isLoading = false,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: projects.length + (isLoading ? 1 : 0),
      itemBuilder: (context, index) {
        if (index == projects.length) {
          return Center(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: CircularProgressIndicator(),
            ),
          );
        }

        final project = projects[index];
        return ProjectCard(
          project: project,
          onTap: () {
            Navigator.of(context).pushNamed(
              '/project-detail',
              arguments: project.id,
            );
          },
        );
      },
    );
  }
}

class ProjectCard extends StatelessWidget {
  final ProjectModel project;
  final VoidCallback? onTap;

  const ProjectCard({
    Key? key,
    required this.project,
    this.onTap,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Image
            if (project.primaryImage != null)
              ClipRRect(
                borderRadius: BorderRadius.vertical(top: Radius.circular(12)),
                child: CachedNetworkImage(
                  imageUrl: project.primaryImage!,
                  height: 200,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  placeholder: (context, url) => Container(
                    height: 200,
                    color: Colors.grey[300],
                    child: Center(child: CircularProgressIndicator()),
                  ),
                  errorWidget: (context, url, error) => Container(
                    height: 200,
                    color: Colors.grey[300],
                    child: Icon(Icons.image_not_supported, size: 50),
                  ),
                ),
              ),
            
            Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Badges
                  Row(
                    children: [
                      if (project.isFeatured)
                        Container(
                          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: Colors.orange,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            'FEATURED',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      SizedBox(width: 8),
                      Container(
                        padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: _getStageColor(project.stage),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          project.stage,
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 8),
                  
                  // Titre
                  Text(
                    project.title,
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  SizedBox(height: 8),
                  
                  // Description
                  Text(
                    project.shortDescription,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                    ),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  SizedBox(height: 12),
                  
                  // Informations
                  Row(
                    children: [
                      Icon(Icons.location_on, size: 16, color: Colors.grey),
                      SizedBox(width: 4),
                      Expanded(
                        child: Text(
                          project.location,
                          style: TextStyle(fontSize: 12, color: Colors.grey),
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Text(
                        project.fundingRange,
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: Theme.of(context).primaryColor,
                        ),
                      ),
                    ],
                  ),
                  SizedBox(height: 8),
                  
                  // Statistiques
                  Row(
                    children: [
                      _buildStat(Icons.visibility, project.viewsCount.toString()),
                      SizedBox(width: 16),
                      _buildStat(Icons.favorite, project.favoritesCount.toString()),
                      SizedBox(width: 16),
                      _buildStat(Icons.star, project.interestsCount.toString()),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStat(IconData icon, String value) {
    return Row(
      children: [
        Icon(icon, size: 14, color: Colors.grey),
        SizedBox(width: 4),
        Text(
          value,
          style: TextStyle(fontSize: 12, color: Colors.grey),
        ),
      ],
    );
  }

  Color _getStageColor(String stage) {
    switch (stage) {
      case 'IDEA':
        return Colors.blue;
      case 'PROTOTYPE':
        return Colors.orange;
      case 'DEVELOPMENT':
        return Colors.purple;
      case 'GROWTH':
        return Colors.green;
      default:
        return Colors.grey;
    }
  }
}
```

## Gestion des erreurs et retry

### Intercepteur de gestion d'erreurs

```dart
// lib/services/error_interceptor.dart
import 'package:dio/dio.dart';
import 'package:connectivity_plus/connectivity_plus.dart';

class ErrorInterceptor extends Interceptor {
  final int maxRetries;
  final Duration retryDelay;

  ErrorInterceptor({
    this.maxRetries = 3,
    this.retryDelay = const Duration(seconds: 2),
  });

  @override
  void onError(DioException error, ErrorInterceptorHandler handler) async {
    if (await _shouldRetry(error)) {
      await _retry(error, handler);
    } else {
      handler.next(error);
    }
  }

  Future<bool> _shouldRetry(DioException error) async {
    // Vérifier la connectivité
    final connectivity = await Connectivity().checkConnectivity();
    if (connectivity == ConnectivityResult.none) {
      return false;
    }

    // Retry sur certains codes d'erreur
    final statusCode = error.response?.statusCode;
    if (statusCode != null) {
      return statusCode >= 500 || statusCode == 408 || statusCode == 429;
    }

    // Retry sur les erreurs de connexion
    return error.type == DioExceptionType.connectionTimeout ||
           error.type == DioExceptionType.receiveTimeout ||
           error.type == DioExceptionType.connectionError;
  }

  Future<void> _retry(DioException error, ErrorInterceptorHandler handler) async {
    final request = error.requestOptions;
    int retryCount = request.extra['retryCount'] ?? 0;

    if (retryCount < maxRetries) {
      await Future.delayed(retryDelay);
      
      request.extra['retryCount'] = retryCount + 1;
      
      try {
        final dio = Dio();
        final response = await dio.request(
          request.path,
          options: Options(
            method: request.method,
            headers: request.headers,
          ),
          data: request.data,
          queryParameters: request.queryParameters,
        );
        handler.resolve(response);
      } catch (e) {
        handler.next(error);
      }
    } else {
      handler.next(error);
    }
  }
}
```

## Bonnes pratiques

### 1. Gestion du cache

```dart
// lib/services/cache_service.dart
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';

class CacheService {
  static const String _projectsKey = 'cached_projects';
  static const Duration _cacheExpiry = Duration(minutes: 15);

  static Future<void> cacheProjects(List<ProjectModel> projects) async {
    final prefs = await SharedPreferences.getInstance();
    final cacheData = {
      'data': projects.map((p) => p.toJson()).toList(),
      'timestamp': DateTime.now().millisecondsSinceEpoch,
    };
    await prefs.setString(_projectsKey, json.encode(cacheData));
  }

  static Future<List<ProjectModel>?> getCachedProjects() async {
    final prefs = await SharedPreferences.getInstance();
    final cachedData = prefs.getString(_projectsKey);
    
    if (cachedData == null) return null;
    
    final data = json.decode(cachedData);
    final timestamp = DateTime.fromMillisecondsSinceEpoch(data['timestamp']);
    
    if (DateTime.now().difference(timestamp) > _cacheExpiry) {
      return null;
    }
    
    return (data['data'] as List)
        .map((json) => ProjectModel.fromJson(json))
        .toList();
  }
}
```

### 2. Upload de fichiers

```dart
// lib/services/upload_service.dart
import 'dart:io';
import 'package:dio/dio.dart';

class UploadService {
  final Dio _dio;

  UploadService(this._dio);

  Future<String> uploadProjectMedia({
    required String projectId,
    required File file,
    required String title,
    String? description,
    required String mediaType,
    Function(double)? onProgress,
  }) async {
    try {
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          file.path,
          filename: file.path.split('/').last,
        ),
        'title': title,
        'description': description ?? '',
        'media_type': mediaType,
      });

      final response = await _dio.post(
        '${ApiConfig.projects}/$projectId/media/',
        data: formData,
        onSendProgress: (sent, total) {
          if (onProgress != null) {
            onProgress(sent / total);
          }
        },
      );

      return response.data['file'];
    } on DioException catch (e) {
      throw _handleError(e);
    }
  }

  String _handleError(DioException error) {
    // Gestion des erreurs similaire aux autres services
    return error.message ?? 'Erreur d\'upload';
  }
}
```

Cette documentation fournit une base solide pour intégrer l'API VentureLink dans une application Flutter, avec des exemples pratiques et les bonnes pratiques de développement mobile. 