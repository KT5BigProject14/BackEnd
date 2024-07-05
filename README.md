# BackEnd
```
BackEnd
├─ .git
│  ├─ config
│  ├─ description
│  ├─ FETCH_HEAD
│  ├─ HEAD
│  ├─ hooks
│  │  ├─ applypatch-msg.sample
│  │  ├─ commit-msg.sample
│  │  ├─ fsmonitor-watchman.sample
│  │  ├─ post-update.sample
│  │  ├─ pre-applypatch.sample
│  │  ├─ pre-commit.sample
│  │  ├─ pre-merge-commit.sample
│  │  ├─ pre-push.sample
│  │  ├─ pre-rebase.sample
│  │  ├─ pre-receive.sample
│  │  ├─ prepare-commit-msg.sample
│  │  ├─ push-to-checkout.sample
│  │  ├─ sendemail-validate.sample
│  │  └─ update.sample
│  ├─ index
│  ├─ info
│  │  └─ exclude
│  ├─ logs
│  │  ├─ HEAD
│  │  └─ refs
│  │     ├─ heads
│  │     │  ├─ develop
│  │     │  └─ ragpipeline
│  │     └─ remotes
│  │        └─ origin
│  │           └─ HEAD
│  ├─ objects
│  │  ├─ info
│  │  └─ pack
│  │     ├─ pack-2ec8e3f623a2e860a6265827a59f22d47321e395.idx
│  │     ├─ pack-2ec8e3f623a2e860a6265827a59f22d47321e395.pack
│  │     └─ pack-2ec8e3f623a2e860a6265827a59f22d47321e395.rev
│  ├─ packed-refs
│  └─ refs
│     ├─ heads
│     │  ├─ develop
│     │  └─ ragpipeline
│     ├─ remotes
│     │  └─ origin
│     │     └─ HEAD
│     └─ tags
├─ .gitignore
├─ alembic
│  ├─ README
│  ├─ script.py.mako
│  └─ versions
│     ├─ 340e8f286de9_new_schema.py
│     ├─ 5f0a01043131_emmail_auth_updated_at.py
│     ├─ 6b13660ef537_emaildb_add.py
│     ├─ 8998e7070e52_new_schema.py
│     ├─ 8f20467982db_signup_modify.py
│     ├─ 946ea6979424_add_table.py
│     ├─ 9b9cc9a4292e_add_table.py
│     ├─ a8d736e26dc1_add_auth_eamil_table.py
│     ├─ bdb51b6a7408_new_schema.py
│     ├─ c405890b02c6_resetting_database.py
│     ├─ c604e06a9a7c_initial_migration.py
│     ├─ cc370a116357_add_faq_table.py
│     ├─ d12e05de07b6_new_schema.py
│     ├─ d3e0f6f5fd2e_add_table.py
│     ├─ e0735d1cf47d_add_faq_table.py
│     └─ e8eeda5e6606_add_auth_eamil_table.py
├─ api
│  ├─ deps.py
│  ├─ main.py
│  └─ routes
│     ├─ login.py
│     ├─ news.py
│     ├─ qna.py
│     ├─ redis.py
│     ├─ user_info.py
│     └─ __init__.py
├─ core
│  ├─ config.py
│  ├─ database.py
│  ├─ redis_config.py
│  └─ __init__.py
├─ crud
│  ├─ info_crud.py
│  ├─ login_crud.py
│  └─ qna_crud.py
├─ documents
│  └─ sample.txt
├─ img
│  ├─ 0i7aYPsvV4WvNBbntffk0A.jpeg
│  ├─ 5GB_DsiApiXYM1XLt-Al1A.jpeg
│  ├─ 8zbzTJQJjXEieTv9Ub2RzQ.jpeg
│  ├─ A0ZMh6Nzd_w-JjIs2EaTwg.jpeg
│  ├─ aauyMxKpDt1l2jLzVKqMdQ.jpeg
│  ├─ APs1pZ8doYjpt32Fe6iVHg.jpeg
│  ├─ BQkkYfwRpSrvmaItr9rjhA.jpeg
│  ├─ BX6oTRylwrIq1VzQm9DY4Q.jpeg
│  ├─ C_ZBf9GTJCpeQqZopRsWpQ.jpeg
│  ├─ dn6w5BqesP0pbxzt46EGxQ.jpeg
│  ├─ ED3ybkdGvAlMr4iinDeb4A.jpeg
│  ├─ fbwM1g7p6pS9zmbjU1UawA.jpeg
│  ├─ gsF3LCctsxrQd0a-o9SA2w.jpeg
│  ├─ hmDnCqW21DahNihRskK2MQ.jpeg
│  ├─ KEsoNoaiwV3uuHu2K0ab6g.jpeg
│  ├─ KxBumFMybQfQScdA7w4d7Q.jpeg
│  ├─ mAH1ShmYby_Sgzsyw6hrDw.jpeg
│  ├─ mEYV-uYZw4k76_KYH8QSKw.jpeg
│  ├─ RFP6A2oumAcyrGfgLzMNww.jpeg
│  ├─ t5PigIi1QGyNDuMt2XJDkg.jpeg
│  ├─ UeAo5KiRNWdWX9FWwmIFWA.jpeg
│  ├─ UqheElJeoCNk6T-hz-8fSQ.jpeg
│  ├─ UYnzoxUyW-vqZpGkZUFQqQ.jpeg
│  ├─ v4bIbve9lebdipIcgIxrzw.jpeg
│  ├─ vFWd4aeZFIvmvx3L24-E0w.jpeg
│  ├─ xiXwgCBLTlJktGLI6xGi5Q.jpeg
│  ├─ xL7XWgCkKVdx27SYSq_HyA.jpeg
│  └─ zd43b7O9rR_4bkf8mMfH6A.jpeg
├─ initial_data.py
├─ LICENSE
├─ main.py
├─ models.py
├─ RAGPipeLine.py
├─ README.md
├─ requirements.txt
├─ schemas.py
├─ service
│  └─ images.py
└─ utils
   ├─ config.py
   ├─ prompt.py
   └─ update.py

```