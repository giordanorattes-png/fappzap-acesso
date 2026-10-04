    // ── FappZap Acesso: serviço instalado pelo pacote da Microsoft Store (MSIX) ─────────────
    // Inserido pelo fappzap/aplicar-marca.py antes do LaunchProcessWin. Fora do pacote, o
    // FzCreateProcess chama o CreateProcessAsUserW exatamente como o RustDesk sempre chamou.
    // Dentro do pacote, o CreateProcessAsUserW do "--server" falhava com o erro 575. Aqui ele
    // tenta em ordem, e anota cada tentativa em %ProgramData%\FappZap-Acesso\fz-lancamento.log:
    //   0) fora do pacote (breakaway) + área de trabalho do usuário (winsta0\default)
    //   1) só a área de trabalho do usuário
    //   2) como o RustDesk faz
    static void FzLog(const wchar_t *fmt, ...)
    {
        wchar_t dir[MAX_PATH];
        if (!ExpandEnvironmentStringsW(L"%ProgramData%\\FappZap-Acesso", dir, MAX_PATH))
            return;
        CreateDirectoryW(dir, NULL);
        std::wstring caminho = std::wstring(dir) + L"\\fz-lancamento.log";
        FILE *f = NULL;
        if (_wfopen_s(&f, caminho.c_str(), L"a") != 0 || !f)
            return;
        SYSTEMTIME st;
        GetLocalTime(&st);
        fwprintf(f, L"%04d-%02d-%02d %02d:%02d:%02d ", st.wYear, st.wMonth, st.wDay, st.wHour, st.wMinute, st.wSecond);
        va_list ap;
        va_start(ap, fmt);
        vfwprintf(f, fmt, ap);
        va_end(ap);
        fwprintf(f, L"\n");
        fclose(f);
    }

    static BOOL FzEmpacotado()
    {
        typedef LONG(WINAPI * PGetCurrentPackageFullName)(UINT32 *, PWSTR);
        PGetCurrentPackageFullName p = (PGetCurrentPackageFullName)GetProcAddress(GetModuleHandleW(L"kernel32.dll"), "GetCurrentPackageFullName");
        UINT32 len = 0;
        return p && p(&len, NULL) == ERROR_INSUFFICIENT_BUFFER;
    }

    static BOOL FzCreateProcess(HANDLE hToken, wchar_t *buf, DWORD flags, LPVOID env, STARTUPINFOW *si, PROCESS_INFORMATION *pi)
    {
        if (!FzEmpacotado())
            return CreateProcessAsUserW(hToken, NULL, buf, NULL, NULL, FALSE, flags, env, NULL, si, pi);
        for (int tentativa = 0; tentativa < 3; tentativa++)
        {
            STARTUPINFOEXW six;
            ZeroMemory(&six, sizeof six);
            six.StartupInfo = *si;
            six.StartupInfo.cb = sizeof(STARTUPINFOW);
            if (tentativa < 2)
                six.StartupInfo.lpDesktop = (LPWSTR)L"winsta0\\default";
            std::vector<BYTE> attrBuf;
            DWORD f = flags;
            DWORD policy = 0x01; // PROCESS_CREATION_DESKTOP_APP_BREAKAWAY_ENABLE_PROCESS_TREE
            BOOL attrOk = FALSE;
            if (tentativa == 0)
            {
                SIZE_T size = 0;
                InitializeProcThreadAttributeList(NULL, 1, 0, &size);
                attrBuf.resize(size);
                six.lpAttributeList = (LPPROC_THREAD_ATTRIBUTE_LIST)attrBuf.data();
                // ProcThreadAttributeValue(18, ...) = PROC_THREAD_ATTRIBUTE_DESKTOP_APP_POLICY
                attrOk = InitializeProcThreadAttributeList(six.lpAttributeList, 1, 0, &size) &&
                         UpdateProcThreadAttribute(six.lpAttributeList, 0, ProcThreadAttributeValue(18, FALSE, TRUE, FALSE), &policy, sizeof policy, NULL, NULL);
                if (attrOk)
                {
                    f |= EXTENDED_STARTUPINFO_PRESENT;
                    six.StartupInfo.cb = sizeof six;
                }
                else
                {
                    FzLog(L"tentativa 0: atributo de breakaway recusado, erro=%lu", GetLastError());
                    six.lpAttributeList = NULL;
                }
            }
            BOOL ok = CreateProcessAsUserW(hToken, NULL, buf, NULL, NULL, FALSE, f, env, NULL, &six.StartupInfo, pi);
            DWORD err = ok ? 0 : GetLastError();
            if (six.lpAttributeList)
                DeleteProcThreadAttributeList(six.lpAttributeList);
            FzLog(L"tentativa %d (breakaway=%d, desktop=%ls): %ls erro=%lu cmd=%ls", tentativa, attrOk,
                  six.StartupInfo.lpDesktop ? six.StartupInfo.lpDesktop : L"(herdado)", ok ? L"OK" : L"FALHOU", err, buf);
            if (ok)
                return TRUE;
            SetLastError(err);
        }
        return FALSE;
    }

