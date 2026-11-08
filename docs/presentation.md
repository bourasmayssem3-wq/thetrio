# Présentation du projet — texte de préparation

## Pitch (environ 3 minutes)

> Bonjour. Notre projet, **The Autonomous FinTech Team**, est un prototype qui montre comment plusieurs agents spécialisés peuvent collaborer pendant un parcours client et financier. Si la clé API est configurée, trois rôles utilisent un modèle OpenAI : la réponse commerciale, l'analyse du feedback et les recommandations stratégiques.
>
> Notre scénario est volontairement simple : une personne s'intéresse à une formation en intelligence artificielle. Le SalesAgent présente l'offre, répond à quelques questions et enregistre l'intérêt. Le Customer Intelligence Agent analyse ensuite le niveau d'expérience et le commentaire du client pour repérer ses besoins, ses objections, ses intérêts et son sentiment.
>
> Avant l'étape financière, le SecurityAgent contrôle le consentement, le montant de démonstration et certaines entrées suspectes. Si le parcours est autorisé, le PaymentAgent simule un paiement. Il peut produire quatre résultats : réussi, refusé, en attente ou annulé. Un paiement en attente est présenté dans une page de validation humaine.
>
> Le Financial Data Analyst Agent calcule les ventes, le taux de conversion, les revenus simulés, les statuts de paiement et les alertes. Le Business Strategy Agent utilise ces indicateurs et les objections détectées pour formuler des recommandations. Le dashboard réunit les métriques, l'historique des parcours et les événements des agents.
>
> Nous avons choisi Python et sa bibliothèque standard pour garder le prototype léger et facile à lancer pendant un hackathon de 14 heures. Les échanges entre agents sont des résultats structurés sauvegardés localement. Le paiement est uniquement simulé : aucune carte ni donnée bancaire n'est demandée.
>
> La valeur du prototype est de rendre le parcours observable et contrôlable : on voit les décisions des agents, les alertes, les résultats et les étapes qui demandent une validation humaine. Les réponses commerciales, l'analyse client et les recommandations peuvent utiliser le modèle OpenAI configuré; sans clé ou en cas d'indisponibilité, elles reviennent aux règles locales. Les calculs financiers, les contrôles de sécurité et le paiement restent déterministes. Les contrôles ne constituent pas un système antifraude de production. Les prochaines étapes pourraient ajouter une interface vocale consentie et un sandbox de paiement autorisé.

## Plan des diapositives

1. **Problématique** — Un parcours client FinTech combine vente, analyse, sécurité, paiement et suivi; les traiter séparément rend les décisions difficiles à suivre.
2. **Notre solution** — Un prototype local qui relie six agents spécialisés pour une formation IA fictive.
3. **Architecture** — Afficher le schéma de [l'architecture](architecture.md); expliquer les entrées/sorties structurées et le rôle de l'orchestrateur.
4. **Démonstration** — Parcours client, analyse de l'objection, contrôle de sécurité et choix de paiement simulé.
5. **Dashboard et sécurité** — Conversion, revenus simulés, statuts, objections, alertes, journal d'événements et validation humaine.
6. **Valeur, limites et suite** — LLM facultatif dans les rôles vente/client/stratégie avec repli local; calculs et sécurité déterministes, aucun paiement réel; voix et sandbox autorisé comme perspectives.

## Démonstration de bout en bout

1. Lancer `python dashboard.py`, puis ouvrir `http://127.0.0.1:8000`.
2. Dans **Customer journey**, demander le prix ou la durée, puis continuer.
3. Choisir **Yes**, sélectionner le niveau d'expérience et écrire un commentaire fictif, par exemple : `I want to learn AI tools but the course is expensive and I am busy`.
4. Donner son consentement pour poursuivre la démonstration.
5. Pour une validation humaine, choisir **Simulate pending**; ouvrir **Human review**, saisir le PIN de démonstration et approuver ou refuser.
6. Ouvrir **Dashboard** et montrer les indicateurs, recommandations, historique et événements des agents.

Pour montrer les autres sorties, recommencer et choisir `Simulate success`, `Simulate refused`, ou `Cancel`. Pour montrer un blocage de sécurité, saisir une phrase de test détectée par la règle anti-prompt-injection dans le commentaire fictif.

## Réponses courtes aux questions possibles

- **Est-ce un vrai paiement ?** Non. Tous les paiements sont simulés et aucun détail de carte n'est collecté.
- **Est-ce un vrai modèle d'IA générative ?** Pour l'analyse client, oui si une clé OpenAI est configurée; sinon le système utilise des règles locales. Les autres agents restent spécialisés et basés sur des règles.
- **Que fait l'humain ?** Il prend la décision finale sur un paiement marqué `pending`.
- **Comment les agents communiquent-ils ?** Ils se passent des dictionnaires Python structurés contenant le statut et les résultats de chaque étape.
- **Pourquoi cette architecture ?** Elle sépare les responsabilités, facilite la démonstration et permet de remplacer progressivement les règles par des composants plus avancés.
