"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

import { useAuthStore } from "@/store/auth-store";

export function AppQueryProvider({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            refetchOnWindowFocus: false,
            refetchOnReconnect: true,
            retry: 1,
            staleTime: 30_000,
            gcTime: 5 * 60_000,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={client}>
      <CacheCleaner queryClient={client} />
      {children}
    </QueryClientProvider>
  );
}

function CacheCleaner({ queryClient }: { queryClient: QueryClient }) {
  const token = useAuthStore((s) => s.accessToken);
  const prevToken = useRef(token);

  useEffect(() => {
    if (prevToken.current && !token) {
      queryClient.clear();
    }
    prevToken.current = token;
  }, [token, queryClient]);

  return null;
}
