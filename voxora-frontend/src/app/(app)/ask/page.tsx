"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import UniversalChat from "@/components/chat/UniversalChat";
import ConversationSummarySidebar from "@/components/chat/ConversationSummarySidebar";
import styles from "./ask.module.css";

function AskContent() {
  const searchParams = useSearchParams();
  const urlConvId = searchParams.get("id");

  return (
    <div className={styles.pageContainer}>
      <div className={styles.mainChatArea}>
        <UniversalChat initialConversationId={urlConvId} isWidget={false} />
      </div>
      <ConversationSummarySidebar />
    </div>
  );
}

export default function AskPage() {
  return (
    <Suspense fallback={<div className={styles.loadingState}>Loading...</div>}>
      <AskContent />
    </Suspense>
  );
}
